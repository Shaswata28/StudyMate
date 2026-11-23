import os
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.v1 import artifacts
from app.core.local_store import database
from app.main import create_app
from app.services.diagram_service import DiagramDraft, SequenceDraft


def test_diagrams():
    draft = DiagramDraft.model_validate({
        "title": "Duplicate check", "missing": "",
        "nodes": [
            {"id": 1, "label": "Validate input", "kind": "step", "source": 1},
            {"id": 2, "label": "Key exists?", "kind": "decision", "source": 1},
            {"id": 3, "label": "Reject duplicate", "kind": "step", "source": 1},
            {"id": 4, "label": "Insert row", "kind": "step", "source": 1},
        ],
        "edges": [
            {"start": 1, "end": 2, "label": ""},
            {"start": 2, "end": 3, "label": "Yes"},
            {"start": 2, "end": 4, "label": "No"},
        ],
    })
    invalid = [
        draft.model_copy(update={"edges": draft.edges[:-1]}),
        draft.model_copy(update={"edges": [draft.edges[0].model_copy(update={"end": 9}), *draft.edges[1:]]}),
        draft.model_copy(update={"nodes": [draft.nodes[0].model_copy(update={"source": 9}), *draft.nodes[1:]]}),
    ]
    for case in invalid:
        try:
            case.mermaid(1)
        except ValueError:
            continue
        raise AssertionError("Invalid graph accepted")
    sequence = SequenceDraft.model_validate({
        "title": "Tutor request", "missing": "",
        "participants": [{"id": 1, "name": "Student"}, {"id": 2, "name": "Tutor"}],
        "messages": [{"start": 1, "end": 2, "label": "Ask a question", "source": 1}],
    })
    assert sequence.mermaid(1) == "sequenceDiagram\n    participant p1 as Student\n    participant p2 as Tutor\n    p1->>p2: Ask a question"
    invalid_sequence = sequence.model_copy(update={"messages": [sequence.messages[0].model_copy(update={"end": 3})]})
    try:
        invalid_sequence.mermaid(1)
    except ValueError:
        pass
    else:
        raise AssertionError("Sequence with unknown participant accepted")

    with TemporaryDirectory() as folder, patch.dict(os.environ, {"STUDYMATE_DATA_DIR": folder}):
        url = "/api/courses/course/artifacts/diagrams"
        with TestClient(create_app()) as client, patch.object(artifacts, "draft_diagram", new_callable=AsyncMock) as generate:
            with database() as db:
                db.execute("INSERT INTO courses VALUES ('course', 'Databases', '', 'stem', '')")
                db.execute("""INSERT INTO materials (id, course_id, name, file_type, file_size, extracted_text, content, created_at, stored_on_disk)
                           VALUES ('keys', 'course', 'Keys', 'text/plain', 1, '', X'', '', 1)""")
                db.execute("INSERT INTO material_index VALUES ('keys', 1, 'Validate input and check the primary key.')")
                turn = db.execute("""INSERT INTO chat_history (course_id, history, created_at)
                    VALUES ('course', '[{"role":"user","content":"How do keys work?"},{"role":"model","content":"Check the key before inserting."}]', '')
                    RETURNING id""").fetchone()["id"]
            generate.side_effect = [invalid[0], draft, sequence, draft.model_copy(update={"missing": "The no outcome is missing."})]
            saved = client.post(url, json={"material_ids": ["keys"]})
            assert saved.status_code == 201, saved.text
            assert generate.await_count == 2
            assert 'n2 -->|"No"| n4' in saved.json()["mermaid"]
            assert saved.json()["sources"][0]["id"] == "keys"
            saved_sequence = client.post(url, json={"turn_id": turn, "diagram_type": "sequence"})
            assert saved_sequence.status_code == 201 and saved_sequence.json()["mermaid"] == sequence.mermaid(1)
            assert client.put(f"{url}/{saved_sequence.json()['id']}", json={"title": "Edited sequence", "mermaid": sequence.mermaid(1)}).is_success
            assert client.post(url, json={"material_ids": ["keys"]}).status_code == 422
            edited = client.put(f"{url}/{saved.json()['id']}", json={"title": "Review keys", "mermaid": "flowchart TD\n A --> B"})
            assert edited.status_code == 200, edited.text
            before_save = generate.await_count
            from_reply = client.post(f"{url}/from-reply/{turn}", json={"mermaid": sequence.mermaid(1)})
            assert from_reply.status_code == 201 and from_reply.json()["mermaid"] == sequence.mermaid(1)
            assert generate.await_count == before_save
            assert client.post(f"{url}/from-reply/9999", json={"mermaid": sequence.mermaid(1)}).status_code == 404
            generate.side_effect = None
            generate.return_value = draft
            repair = client.post(f"{url}/from-reply/{turn}/repair", json={
                "mermaid": "flowchart TD\n A[", "parser_error": "Unclosed node label",
            })
            assert repair.status_code == 200 and repair.json()["mermaid"] == draft.mermaid(1)
            assert "Unclosed node label" in generate.await_args.args[0]
        with TestClient(create_app()) as client:
            assert {row["title"] for row in client.get(url).json()} == {"Review keys", "Edited sequence", "How do keys work?"}


if __name__ == "__main__":
    test_diagrams()
