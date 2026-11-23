import json
import os
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.v1 import chat
from app.main import create_app

from app.api.v1.chat import prepare_turn
from app.core.config import settings
from app.core.local_store import database, initialize_database


def test_course_context():
    with TemporaryDirectory() as folder, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": folder}), patch.object(settings, "EMBEDDING_MODEL", ""):
        initialize_database()
        with database() as db:
            db.execute("INSERT INTO courses VALUES ('course', 'Physics', '', 'stem', '')")
            for key, passage in [
                ("motion", "In a closed system, total momentum is conserved. Cobalt flywheel: measured angular momentum remained constant at 12 kg m squared per second."),
                ("energy", "Kinetic energy decreases in an inelastic collision. Jade collision: kinetic energy decreased from 20 J to 12 J."),
            ]:
                db.execute("""
                    INSERT INTO materials (id, course_id, name, file_type, file_size, extracted_text, content, created_at, stored_on_disk)
                    VALUES (?, 'course', ?, 'application/pdf', 1, '', X'', '', 1)
                """, (key, key + ".pdf"))
                db.execute("INSERT INTO material_index VALUES (?, 2, ?)", (key, passage))

        _, _, sources, _ = prepare_turn("course", "Explain momentum.")
        assert sources[0]["page"] == 2 and sources[0]["passage_hash"]
        with database() as db:
            db.execute("INSERT INTO chat_history (course_id, history, created_at) VALUES ('course', ?, '')", (json.dumps([
                {"role": "user", "content": "Explain momentum."},
                {"role": "model", "content": "It stays constant.", "sources": sources},
            ]),))
        assert prepare_turn("course", "Diagram that.")[2] == sources
        assert prepare_turn("course", "What is photosynthesis?", "motion")[2] == []
        assert prepare_turn("course", "Diagram that.", "energy")[2] == []
        prompt, _, both, _ = prepare_turn("course", "Explain momentum and explain inelastic collisions.")
        assert {source["id"] for source in both} == {"motion", "energy"}
        assert "requested parts 1" in prompt and "requested parts 2" in prompt
        with TestClient(create_app()) as client, patch.object(chat, "generate_chat", new_callable=AsyncMock) as generate:
            url = "/api/courses/course/chat"
            response = client.post(url, json={"message": "What is photosynthesis?", "material_id": "motion"})
            assert response.status_code == 201 and "couldn't find" in response.json()["response"]
            generate.assert_not_called()
            generate.return_value = "Momentum is conserved [Source 1]. Incorrect reference [Source 9]."
            response = client.post(url, json={"message": "Explain momentum."})
            assert response.status_code == 201 and "[Source 1]" in response.json()["response"]
            assert "[Source 9]" not in response.json()["response"]
            generate.assert_awaited_once()
            client.post(url, json={"message": "Compare momentum and kinetic energy."}).raise_for_status()
            generate.reset_mock()
            response = client.post(url, json={"message": "Explain that."})
            assert response.status_code == 201
            assert response.json()["response"] == "Which should I focus on: momentum or kinetic energy?"
            generate.assert_not_called()
            response = client.post(url, json={"message": "Why did the Jade collision gain kinetic energy? Cite the excerpt."})
            reply = response.json()["response"]
            assert response.status_code == 201
            assert "opposite change" in reply and "decreased from 20 J to 12 J" in reply and "[Source 1]" in reply
            response = client.post(url, json={"message": "What is the Cobalt flywheel's measured angular momentum and its mass? Cite the excerpt."})
            reply = response.json()["response"]
            assert response.status_code == 201
            assert "12 kg m squared per second" in reply and "do not report its mass" in reply and "[Source 1]" in reply
            generate.assert_not_called()
            artifact_url = "/api/courses/course/artifacts/context"
            prepared = client.post(artifact_url, json={"material_ids": ["motion", "energy"]}).json()
            assert {entry["source"]["id"] for entry in prepared["evidence"]} == {"motion", "energy"}
            assert client.post(artifact_url, json={"material_ids": ["missing"]}).status_code == 404
            assert client.post(artifact_url, json={"material_ids": ["motion"], "turn_id": 1}).status_code == 422
            turn_id = response.json()["id"]
            prepared = client.post(artifact_url, json={"turn_id": turn_id}).json()
            assert "Cobalt" in prepared["original_question"]
            assert any("12 kg" in entry["text"] for entry in prepared["evidence"])
            with database() as db:
                db.execute("INSERT INTO courses VALUES ('other', 'Other course', '', 'general', '')")
                db.execute("UPDATE materials SET processing_status='indexing' WHERE id='energy'")
                db.execute("UPDATE material_index SET text='Revised measurement: 90 kg.' WHERE material_id='motion'")
            assert client.post("/api/courses/other/artifacts/context", json={"turn_id": turn_id}).status_code == 404
            assert client.post("/api/courses/other/artifacts/context", json={"material_ids": ["motion"]}).status_code == 404
            assert client.post(artifact_url, json={"material_ids": ["energy"]}).status_code == 409
            prepared = client.post(artifact_url, json={"turn_id": turn_id}).json()
            assert any(source["id"] == "motion" for source in prepared["unavailable_sources"])
            assert all(entry["source"]["id"] != "motion" for entry in prepared["evidence"])
            generate.return_value = "A diagram reply"
            diagram = client.post(url, json={"message": "Can you generate a digram showing how a Python web framework works?"})
            assert diagram.status_code == 201
            assert generate.await_args.kwargs == {"flowchart": True}


if __name__ == "__main__":
    test_course_context()
