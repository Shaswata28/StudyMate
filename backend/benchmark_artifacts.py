"""Run the local Phase 0 artifact benchmark with python benchmark_artifacts.py."""

import json
from time import perf_counter

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.services.local_setup import MODELS


class Item(BaseModel):
    title: str
    text: str
    sources: list[str]


class Draft(BaseModel):
    items: list[Item]


EVIDENCE = {
    "P1": "In a closed system, the total momentum remains constant throughout a collision.",
    "P2": "In the inelastic cart trial, kinetic energy fell from 20 J to 12 J. The test did not record collision duration.",
    "D1": "A database primary key uniquely identifies each row and cannot be null.",
    "D2": "After validating the input, check whether the primary key already exists. Reject duplicates. Otherwise insert the row.",
}
CASES = [
    ("diagram", "Write three labeled flowchart nodes and express their connections, including both branches.", ["D2"]),
    ("flashcards", "Write exactly two flashcards. Put the question in title and answer in text.", ["D1", "P1"]),
    ("quiz", "Write one quiz question about the change in kinetic energy. Include the correct answer and explanation.", ["P2"]),
    ("notes", "Write two short notes covering momentum and the cart trial's kinetic energy values.", ["P1", "P2"]),
    ("slides", "Outline two slides, one on primary keys and one on duplicate handling.", ["D1", "D2"]),
    ("ambiguous", "The previous discussion mentioned primary keys and momentum. Diagram that. Ask one clarification.", ["D1", "P1"]),
    ("missing", "State the measured collision duration or explain why it cannot be given.", ["P2"]),
]


def main():
    schema = Draft.model_json_schema()
    with httpx.Client(base_url=settings.OLLAMA_BASE_URL, timeout=120) as client:
        installed = {model["name"] for model in client.get("/api/tags").raise_for_status().json()["models"]}
        for model, _, _ in MODELS:
            if model not in installed:
                print(json.dumps({"model": model, "status": "unavailable"}), flush=True)
                continue
            for case, task, source_ids in CASES:
                excerpts = "\n".join(f"{key}: {EVIDENCE[key]}" for key in source_ids)
                started = perf_counter()
                result = {"model": model, "case": case}
                try:
                    response = client.post("/api/chat", json={
                        "model": model, "stream": False, "think": False, "format": schema,
                        "options": {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 768},
                        "messages": [
                            {"role": "system", "content": (
                                "Create a short study draft using the supplied excerpts. Cite excerpt IDs "
                                "in each item's sources. For clarification or missing evidence, use one "
                                "item and cite only evidence used. Return JSON matching this schema: " + json.dumps(schema)
                            )},
                            {"role": "user", "content": f"{task}\n\n{excerpts}"},
                        ],
                    }).raise_for_status().json()
                    result["seconds"] = round(perf_counter() - started, 2)
                    draft = Draft.model_validate_json(response["message"]["content"])
                    result.update(
                        schema_valid=True,
                        source_ids_valid=bool(draft.items) and all(
                            set(item.sources) <= set(source_ids) and (item.sources or case == "ambiguous")
                            for item in draft.items
                        ),
                        items=draft.model_dump()["items"],
                    )
                except ValidationError as error:
                    result.update(schema_valid=False, error=str(error))
                except httpx.HTTPError as error:
                    result["error"] = str(error)
                print(json.dumps(result, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
