import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from time import monotonic, sleep
from urllib.parse import urlsplit

import httpx
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.v1 import chat
from app.main import create_app


def wait_for_material(client, materials_url, material_id, expected="completed"):
    deadline = monotonic() + 8
    while monotonic() < deadline:
        rows = client.get(materials_url).json()
        item = next(row for row in rows if row["id"] == material_id)
        if item["processing_status"] == expected:
            return item
        assert item["processing_status"] != "failed", item
        sleep(.05)
    raise AssertionError(f"Material {material_id} did not reach {expected}")


def test_local_study_session_survives_restart():
    with TemporaryDirectory() as data_dir, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": data_dir}):
        with TestClient(create_app()) as client:
            assert client.get("/api/profile").json() is None
            assert client.post("/api/auth/login").status_code == 404
            profile = {"name": "Student", "academic": {"grade": "Undergraduate", "subject": "Chemistry"},
                       "avatar": None, "institution": "College", "goal": "Prepare for finals", "terms_accepted": True}
            assert client.put("/api/profile", json=profile, headers={"Origin": "https://example.com"}).status_code == 403
            assert client.put("/api/profile", json=profile).json() == profile
            assert client.post("/api/profile/preferences", json={"technical_language": 0.9}).status_code == 200
            course = client.post("/api/courses", json={"name": "Chemistry", "subject_profile": "life_sciences"})
            assert course.status_code == 201
            url = f"/api/courses/{course.json()['id']}"
            upload = client.post(f"{url}/materials", files={
                "file": ("notes.txt", ("Filler " * 300 + "Catalysts lower activation energy.").encode(), "text/plain"),
            })
            assert upload.status_code == 201, upload.text
            wait_for_material(client, f"{url}/materials", upload.json()["id"])
            with patch.object(chat, "generate_chat", new_callable=AsyncMock, return_value="Tutor response") as model:
                first = client.post(f"{url}/chat", json={"message": "Explain catalysts"})
                assert first.status_code == 201, first.text
                assert client.get(f"{url}/chat").json()[-1]["id"] == first.json()["id"]
                prompt, history, _, _ = model.await_args.args
                assert "Undergraduate" in prompt
                assert "rigorous notation" in prompt
                assert "Explain mechanisms" in prompt
                assert "Catalysts lower activation energy" in prompt
                assert not history
                for message in ("Question two", "Question three", "Question four"):
                    assert client.post(f"{url}/chat", json={"message": message}).status_code == 201

        with TestClient(create_app()) as reopened:
            assert reopened.get("/api/profile").json() == profile
            assert reopened.get("/api/profile/preferences").json()["prefs"]["technical_language"] == 0.9
            assert reopened.get("/api/courses").json()[0]["subject_profile"] == "life_sciences"
            assert len(reopened.get(f"{url}/materials").json()) == 1
            with patch.object(chat, "generate_chat", new_callable=AsyncMock, return_value="Follow-up") as model:
                assert reopened.post(f"{url}/chat", json={"message": "What about the last step?"}).status_code == 201
                prompt, history, _, _ = model.await_args.args
                assert "Optional presentation style" not in prompt
                assert "Undergraduate" not in prompt
                assert "Never invent citations" in prompt
                assert [entry["content"] for entry in history if entry["role"] == "user"] == [
                    "Question two", "Question three", "Question four",
                ]
            with patch.object(chat, "generate_chat", new_callable=AsyncMock, side_effect=ConnectionError):
                assert reopened.post(f"{url}/chat", json={"message": "Offline model unavailable"}).status_code == 503
            assert len(reopened.get(f"{url}/chat").json()) == 5
            assert reopened.delete(url).status_code == 200
            assert reopened.get(f"{url}/chat").status_code == 404


def test_study_overview_and_local_tools():
    from app.api.v1 import study

    def fake_whisper(command, **kwargs):
        output = Path(command[command.index("-of") + 1]).with_suffix(".txt")
        output.write_text("Explain momentum.", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    with TemporaryDirectory() as folder, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": folder}):
        with TestClient(create_app()) as client:
            settings = {"profile": {"name": "Learner"}, "prefs": {"structure_preference": 0.9}}
            assert client.put("/api/profile/settings", json=settings).status_code == 200
            assert client.get("/api/profile/preferences").json()["prefs"]["structure_preference"] == 0.9
            course = client.post("/api/courses", json={"name": "Physics"}).json()["id"]
            other = client.post("/api/courses", json={"name": "Writing"}).json()["id"]
            import pymupdf
            with pymupdf.open() as document:
                document.new_page().insert_text((72, 72), "Momentum equals mass times velocity.")
                document.new_page().insert_text((72, 72), "Review exercises.")
                content = document.tobytes()
            material = client.post(f"/api/courses/{course}/materials", files={
                "file": ("notes.pdf", content, "application/pdf"),
            }).json()
            wait_for_material(client, f"/api/courses/{course}/materials", material["id"])
            with patch.object(chat, "generate_chat", new_callable=AsyncMock, return_value="Momentum equals mass times velocity. [Source 1]") as model:
                request = {"message": "Explain this attachment.", "material_id": material["id"]}
                assert client.post(f"/api/courses/{other}/chat", json=request).status_code == 404
                answer = client.post(f"/api/courses/{course}/chat", json=request)
                assert answer.status_code == 201
                turn_id = answer.json()["id"]
                bookmark = f"/api/courses/{course}/chat/{turn_id}/bookmark"
                assert client.put(f"/api/courses/{other}/chat/{turn_id}/bookmark?saved=true").status_code == 404
                assert client.put(bookmark + "?saved=true").json() == {"bookmarked": True}
                assert client.put(bookmark + "?saved=true").json() == {"bookmarked": True}
                turn = client.get(f"/api/courses/{course}/chat").json()[0]
                assert turn["bookmarked"]
                assert turn["history"][1]["sources"][0]["id"] == material["id"]
                source_url = f"/api/courses/{course}/materials/{material['id']}"
                assert client.get(source_url + "?page=2").json()["text"] == "Review exercises."
                assert client.get(source_url + "?page=3").status_code == 404
                assert client.get(source_url + "/file").content == content
                assert client.get(f"/api/courses/{other}/materials/{material['id']}").status_code == 404
                assert "Momentum equals mass times velocity." in model.await_args.args[0]
                with patch.object(chat.settings, "LLM_VISION_MODEL", ""):
                    response = client.post(f"/api/courses/{course}/chat", json={
                        "message": "Explain this image.", "attachments": [{
                            "filename": "notes.png", "mime_type": "image/png", "data": "aW1hZ2U=",
                        }],
                    })
                assert response.status_code == 201
                assert model.await_args.args[3] == [b"image"]
            summary = client.get("/api/study").json()
            assert (summary["courses"], summary["materials"], summary["turns"]) == (2, 1, 2)
            assert summary["recent"][0]["question"] == "Explain this image."
            with patch.object(study, "whisper_available", return_value=True), patch.object(study, "run", side_effect=fake_whisper):
                response = client.post("/api/transcribe", files={"audio": ("test.wav", b"RIFF0000WAVE", "audio/wav")})
                assert response.json() == {"text": "Explain momentum."}
                assert client.post("/api/transcribe", files={"audio": ("bad.wav", b"bad", "audio/wav")}).status_code == 422
        with TestClient(create_app()) as reopened:
            assert reopened.get(f"/api/courses/{course}/chat").json()[0]["bookmarked"]
            assert reopened.put(bookmark + "?saved=false").json() == {"bookmarked": False}
            assert not reopened.get(f"/api/courses/{course}/chat").json()[0]["bookmarked"]


def test_model_setup():
    from app import main

    compact, balanced, _ = [candidate[0] for candidate in main.MODELS]
    with TemporaryDirectory() as directory, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": directory}):
        with TestClient(create_app()) as client:
            device = client.get("/api/settings/device")
            assert device.status_code == 200
            assert device.json()["recommended"] in {candidate["id"] for candidate in device.json()["models"]}
            assert client.post("/api/settings/model?model=unsupported").status_code == 422
            with patch.object(main, "ensure_ollama", return_value={compact, balanced}) as runtime:
                assert client.post("/api/settings/model", params={"model": balanced}).status_code == 200
                runtime.assert_called_once_with(True)
                assert client.get("/api/settings").json()["model"] == balanced
            with patch.object(main, "install_voice") as install:
                assert client.post("/api/settings/voice").json() == {"status": "ready"}
                install.assert_called_once_with()
        with TestClient(create_app()) as reopened, patch.object(main, "ensure_ollama", return_value={balanced}):
            assert reopened.get("/api/settings").json()["status"] == "ready"
            assert reopened.get("/api/settings").json()["model"] == balanced


def test_pdf_upload():
    import pymupdf

    with TemporaryDirectory() as directory, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": directory}):
        with TestClient(create_app()) as client, pymupdf.open() as document:
            course = client.post("/api/courses", json={"name": "Physics"}).json()["id"]
            page = document.new_page()
            page.insert_text((72, 72), "Momentum equals mass times velocity.")
            content = document.tobytes()
            url = f"/api/courses/{course}/materials"
            response = client.post(url, files={"file": ("physics.pdf", content, "application/octet-stream")})
            assert response.status_code == 201, response.text
            assert response.json()["processing_status"] == "queued"
            wait_for_material(client, url, response.json()["id"])
            preview = client.get(f"{url}/{response.json()['id']}?page=1")
            assert "Momentum equals mass times velocity." in preview.json()["text"]
            assert client.get(f"{url}/{response.json()['id']}/file").content == content
            invalid = client.post(url, files={"file": ("broken.pdf", b"invalid", "application/pdf")})
            assert invalid.status_code == 201
            failure = wait_for_material(client, url, invalid.json()["id"], "failed")
            assert failure["processing_error"]
            assert client.get(f"{url}/{invalid.json()['id']}").status_code == 409
            assert client.get(f"{url}/{invalid.json()['id']}/file").status_code == 409


def test_background_embeddings_gate_access():
    from app.services import material_indexer, rag_service

    started, release = Event(), Event()

    def embed(request):
        body = json.loads(request.content)
        inputs = body["input"]
        if isinstance(inputs, list):
            assert len(inputs) <= 8
            started.set()
            assert release.wait(5)
        return httpx.Response(200, json={"embeddings": [[1, 0] for _ in (inputs if isinstance(inputs, list) else [inputs])]})

    with TemporaryDirectory() as directory, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": directory}), patch.object(chat.settings, "EMBEDDING_MODEL", "test-embed"):
        with TestClient(create_app()) as client:
            course = client.post("/api/courses", json={"name": "Science"}).json()["id"]
            materials = f"/api/courses/{course}/materials"
            original_client = httpx.Client
            with patch.object(material_indexer.httpx, "Client", side_effect=lambda **_: original_client(transport=httpx.MockTransport(embed))):
                uploaded = client.post(materials, files={"file": ("source.txt", b"Momentum and inertia", "text/plain")})
                material_id = uploaded.json()["id"]
                try:
                    assert uploaded.json()["processing_status"] == "queued"
                    assert started.wait(5)
                    assert client.get(materials).json()[0]["processing_status"] == "embedding"
                    assert client.get(f"{materials}/{material_id}").status_code == 409
                    result = client.post(f"/api/courses/{course}/chat", json={
                        "message": "Explain this attachment", "material_id": material_id,
                    })
                    assert result.status_code == 409
                finally:
                    release.set()
                wait_for_material(client, materials, material_id)
            with patch.object(rag_service.httpx, "post", return_value=httpx.Response(
                200, request=httpx.Request("POST", "http://local.test/api/embed"), json={"embeddings": [[1, 0]]},
            )), patch.object(chat, "generate_chat", new_callable=AsyncMock, return_value="Tutor answer") as tutor:
                assert client.post(f"/api/courses/{course}/chat", json={"message": "Why resist speeding up?"}).status_code == 201
                assert "Momentum and inertia" in tutor.await_args.args[0]


def test_materials_larger_than_old_limit():
    from app.api.v1 import materials
    from app.core.local_store import material_path
    from app.services import material_indexer

    size = 51 * 1024 * 1024
    with TemporaryDirectory() as directory, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": directory}):
        with TestClient(create_app()) as client, TemporaryFile() as source:
            course = client.post("/api/courses", json={"name": "Large files"}).json()["id"]
            route = f"/api/courses/{course}/materials"
            source.truncate(size)
            with patch.object(material_indexer.ocr_service, "pages", return_value=[(1, "Test passage")]):
                reply = client.post(route, files={"file": ("large.pdf", source, "application/pdf")})
                assert reply.status_code == 201, reply.text
                item = reply.json()
                assert item["file_size"] == size
                assert material_path(course, item["id"]).stat().st_size == size
                wait_for_material(client, route, item["id"])
            with patch.object(materials, "disk_usage") as disk:
                disk.return_value.free = 1
                rejected = client.post(route, files={"file": ("small.txt", b"hello", "text/plain")})
                assert rejected.status_code == 507
                assert len(client.get(route).json()) == 1


def check_static_export():
    web_root = Path(os.environ["STUDYMATE_WEB_ROOT"]) if os.getenv("STUDYMATE_WEB_ROOT") else Path(__file__).resolve().parents[1] / "frontend" / "out"
    if not web_root.is_dir():
        return
    with TemporaryDirectory() as data_dir, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": data_dir}):
        with TestClient(create_app(web_root)) as client:
            for route in ("/", "/app/", "/onboarding/", "/questions/", "/settings/"):
                assert client.get(route).status_code == 200, route
            assert client.get("/api/profile").json() is None
            assert client.get("/login/").status_code == 404
            settings = client.get("/settings/").text
            for category in ("Learning", "Appearance", "Local setup"):
                assert category in settings
            for name in ("InstrumentSans.ttf", "InstrumentSerif-Regular.ttf"):
                asset = client.get(f"/fonts/{name}")
                assert asset.status_code == 200 and asset.content[:4] == bytes.fromhex("00010000")


class FakeOllama(BaseHTTPRequestHandler):
    model = "qwen3.5:0.8b-q8_0"
    downloaded = False

    def reply(self, body: dict, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode() + b"\n")

    def do_GET(self):
        assert self.path == "/api/tags"
        self.reply({"models": [{"name": self.model}] if self.downloaded else []})

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert request["model"] == self.model
        if self.path == "/api/pull":
            assert request["stream"]
            type(self).downloaded = True
            self.reply({"status": "success"}, "application/x-ndjson")
        else:
            assert self.path == "/api/chat"
            assert "check units" in request["messages"][0]["content"]
            assert request["options"]["num_ctx"] == 4096
            assert request["think"] is False
            self.reply({"message": {"role": "assistant", "content": "A locally generated test answer."}, "done": True})

    def log_message(self, *args):
        pass


def check_launcher(command: list[str]):
    with TemporaryDirectory() as data_dir, ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama) as ollama_server:
        thread = Thread(target=ollama_server.serve_forever, daemon=True)
        thread.start()
        environment = {
            **os.environ,
            "STUDYMATE_DATA_DIR": data_dir,
            "STUDYMATE_NO_BROWSER": "1",
            "OLLAMA_BASE_URL": f"http://127.0.0.1:{ollama_server.server_port}",
            "LLM_CORE_MODEL": FakeOllama.model,
            "LLM_CONTEXT_SIZE": "4096",
            "STUDYMATE_WEB_ROOT": "",
        }
        try:
            with subprocess.Popen(command, env=environment, stdout=subprocess.PIPE, text=True) as launcher:
                try:
                    first_line = launcher.stdout.readline()
                    assert "StudyMate is opening at " in first_line, first_line
                    url = first_line.split()[4].rstrip(".")
                    assert urlsplit(url).hostname == "127.0.0.1"
                    with httpx.Client(base_url=url, timeout=5) as client:
                        deadline = monotonic() + 15
                        while True:
                            try:
                                assert client.get("/health").status_code == 200
                                break
                            except httpx.ConnectError:
                                if monotonic() >= deadline:
                                    raise
                                sleep(0.1)

                        assert client.get("/").status_code == 200
                        assert client.get("/api/settings").json()["status"] == "missing"
                        assert client.post("/api/settings/model").json()["status"] == "ready"
                        assert client.get("/api/settings").json()["status"] == "ready"
                        assert client.put("/api/profile", json={"name": "Student"}).status_code == 200
                        course = client.post("/api/courses", json={"name": "Physics", "subject_profile": "stem"}).json()
                        response = client.post(f"/api/courses/{course['id']}/chat", json={"message": "Explain kinetic energy"})
                        assert response.json()["response"] == "A locally generated test answer.", response.text
                finally:
                    launcher.terminate()
        finally:
            ollama_server.shutdown()
    print("Student launcher and Ollama API integration checks passed.")


if __name__ == "__main__":
    test_local_study_session_survives_restart()
    test_study_overview_and_local_tools()
    test_model_setup()
    test_pdf_upload()
    test_background_embeddings_gate_access()
    test_materials_larger_than_old_limit()
    check_static_export()
    print("Local profile, storage, tutoring, and static serving checks passed.")
    if len(sys.argv) > 1:
        check_launcher(sys.argv[1:])
