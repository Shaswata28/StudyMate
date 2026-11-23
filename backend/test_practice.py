import json
import os
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.v1 import practice
from app.core.local_store import database
from app.main import create_app


def test_practice():
    with TemporaryDirectory() as folder, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": folder}):
        content = {
            "source": 1, "question": "What does the tutor receive?", "answer": "A prompt",
            "explanation": "The excerpt says StudyMate sends a prompt.",
        }
        flashcard = {**content, "choices": []}
        quiz = {"source": 1, "sentence": "StudyMate sends a prompt to the tutor.", "choices": ["a prompt", "An image", "A file"], "correct_choice": 0}
        responses = [flashcard, quiz]
        chat = AsyncMock(side_effect=[
            SimpleNamespace(message=SimpleNamespace(content=json.dumps({"items": [item]}))) for item in responses
        ])
        base = "/api/courses/course/artifacts/practice"
        with TestClient(create_app()) as client, patch.object(practice, "ollama_client", return_value=SimpleNamespace(chat=chat)):
            with database() as db:
                db.execute("INSERT INTO courses VALUES ('course', 'Tutor', '#456789', 'stem', '')")
                db.execute("""INSERT INTO materials (id, course_id, name, file_type, file_size, extracted_text, content, created_at, stored_on_disk)
                    VALUES ('notes', 'course', 'Tutor notes', 'text/plain', 1, '', X'', '', 1)""")
                db.execute("INSERT INTO material_index VALUES ('notes', 1, 'StudyMate sends a prompt to the tutor.')")
            assert client.get("/api/study").json()["due_flashcards"] == 0
            card_response = client.post(base, json={"material_ids": ["notes"], "kind": "flashcard"})
            assert card_response.status_code == 201, card_response.text
            card = card_response.json()[0]
            assert client.get("/api/study").json()["due_flashcards"] == 1
            quiz_response = client.post(base, json={"material_ids": ["notes"], "kind": "quiz"})
            assert quiz_response.status_code == 201, quiz_response.text
            question = quiz_response.json()[0]
            attempt = {"choice": "An image", "revision": question["revision"]}
            missed = client.post(f"{base}/{question['id']}/review", json=attempt)
            assert missed.status_code == 200 and missed.json()["correct"] is False
            assert missed.json()["item"]["evidence"]["text"] == "StudyMate sends a prompt to the tutor."
            assert client.post(f"{base}/{question['id']}/review", json=attempt).status_code == 409
            edit = {"question": "Edited question", "answer": card["answer"], "explanation": card["explanation"], "choices": [], "revision": card["revision"]}
            edited = client.put(f"{base}/{card['id']}", json=edit)
            assert edited.status_code == 200
            remembered = client.post(f"{base}/{card['id']}/review", json={"recalled": True, "revision": edited.json()["revision"]})
            assert remembered.status_code == 200 and remembered.json()["correct"] is True
        with TestClient(create_app()) as client:
            assert client.get("/api/study").json()["due_flashcards"] == 0
            items = {item["id"]: item for item in client.get(base).json()}
            assert items[card["id"]]["question"] == "Edited question"
            assert items[question["id"]]["due_at"] < items[card["id"]]["due_at"]
            with database() as db:
                assert db.execute("SELECT count(*) FROM study_reviews").fetchone()[0] == 2


if __name__ == "__main__":
    test_practice()
