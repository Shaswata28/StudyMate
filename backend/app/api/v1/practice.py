import json
import re
from time import time
from typing import Annotated, Literal

import httpx
import ollama
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, PositiveInt, ValidationError, model_validator
from starlette.concurrency import run_in_threadpool

from app.api.v1.artifacts import ArtifactContextRequest, artifact_context
from app.api.v1.courses import require_course
from app.core.config import settings
from app.core.local_store import database
from app.services.llm_service import ollama_client

router = APIRouter(tags=["practice"])
Kind = Literal["flashcard", "quiz"]
BASE = "/courses/{course_id}/artifacts/practice"
DAY = 86400


class CardContent(BaseModel):
    question: str = Field(min_length=1, max_length=300)
    answer: str = Field(min_length=1, max_length=400)
    explanation: str = Field(min_length=1, max_length=650)
    choices: list[str] = Field(max_length=4)

    @model_validator(mode="after")
    def validate_content(self):
        self.question = self.question.strip()
        self.answer = self.answer.strip()
        self.explanation = self.explanation.strip()
        self.choices = [choice.strip() for choice in self.choices]
        if not all((self.question, self.answer, self.explanation)):
            raise ValueError("Enter a question, answer, and explanation.")
        if self.choices and (
            len(self.choices) < 2 or len({choice.casefold() for choice in self.choices}) != len(self.choices)
            or self.answer not in self.choices or any(not choice or len(choice) > 400 for choice in self.choices)
        ):
            raise ValueError("Use distinct choices and include the correct answer among them.")
        return self


class DraftCard(CardContent):
    source: PositiveInt


class DraftCards(BaseModel):
    items: list[DraftCard] = Field(max_length=3)


class DraftQuizItem(BaseModel):
    sentence: str = Field(min_length=8, max_length=300)
    choices: list[Annotated[str, Field(min_length=1, max_length=30)]] = Field(min_length=3, max_length=3)
    correct_choice: Literal[0, 1, 2]
    source: PositiveInt


class DraftQuiz(BaseModel):
    items: list[DraftQuizItem] = Field(max_length=2)


class PracticeRequest(ArtifactContextRequest):
    kind: Kind


class PracticeEdit(CardContent):
    revision: int = Field(ge=0)


class Review(BaseModel):
    revision: int = Field(ge=0)
    recalled: bool | None = None
    choice: str | None = Field(default=None, max_length=400)


def item_data(row):
    item = dict(row)
    item["evidence"] = json.loads(item["evidence"])
    content = json.loads(item.pop("content"))
    return {**item, **content}


def quiz_card(item: DraftQuizItem, evidence: list[dict]) -> DraftCard | None:
    if item.source > len(evidence):
        return None
    excerpt = " ".join(evidence[item.source - 1]["text"].split())
    sentence = " ".join(item.sentence.split())
    answer = item.choices[item.correct_choice].strip()
    if not answer or sentence not in excerpt:
        return None
    span = re.compile(rf"(?<!\w){re.escape(answer)}(?!\w)", re.I)
    if len(span.findall(sentence)) != 1:
        return None
    question = span.sub("____", sentence)
    if not any(letter.isalnum() for letter in question):
        return None
    return DraftCard(question=question, answer=answer, explanation=f"The source reads: {sentence}",
                     choices=item.choices, source=item.source)


def require_item(db, course_id, item_id):
    item = db.execute("SELECT * FROM study_items WHERE course_id=? AND id=?", (course_id, item_id)).fetchone()
    if item is None:
        raise HTTPException(404, "Study item not found in this course.")
    return item_data(item)


@router.get(BASE)
def list_items(course_id: str):
    with database() as db:
        require_course(db, course_id)
        return [item_data(row) for row in db.execute(
            "SELECT * FROM study_items WHERE course_id=? ORDER BY due_at, id", (course_id,)
        )]


@router.post(BASE, status_code=201)
async def create_items(course_id: str, request: PracticeRequest):
    context = await run_in_threadpool(artifact_context, course_id, request)
    evidence = context["evidence"]
    if not evidence:
        raise HTTPException(422, "Select ready material or a reply with available sources.")
    quiz = request.kind == "quiz"
    schema = (DraftQuiz if quiz else DraftCards).model_json_schema()
    schema["$defs"]["DraftQuizItem" if quiz else "DraftCard"]["properties"]["source"]["enum"] = list(range(1, len(evidence) + 1))
    detail = (
        "Write one or two fill-in-the-blank multiple-choice items. Copy a complete sentence verbatim "
        "from the source into sentence, with its original punctuation and no blank. Give exactly three "
        "distinct words or short phrases, including one copied exactly from that sentence. "
        "For example, a sentence 'Water covers the planet.' can have choices ['Air','Water','Sand'] "
        "and correct_choice 1. Never use a whole sentence as a choice. "
        "Set correct_choice to the zero-based index of that copied choice. The app makes the blank."
        if quiz else "Write up to three short flashcards and set choices to an empty array."
    )
    excerpts = "\n\n".join(f"Source {index}: {entry['text']}" for index, entry in enumerate(evidence, 1))
    try:
        response = await ollama_client().chat(
            model=settings.tutor_model, stream=False, think=False, format=schema,
            options={"temperature": 0, "num_ctx": settings.LLM_CONTEXT_SIZE, "num_predict": settings.LLM_MAX_RESPONSE_TOKENS},
            messages=[
                {"role": "system", "content": (
                    f"{detail} Include one source number for each item. "
                    + ("Base all answers on the numbered excerpt. " if quiz else "Include a short explanation based only on that excerpt. ")
                    +
                    "Return an empty list if there is not enough evidence for the requested topic."
                )},
                {"role": "user", "content": f"Topic: {context['question'] or 'Key facts in these sources'}\n\n{excerpts}"},
            ],
        )
        raw = response.message.content or ""
        if quiz:
            drafts = [card for item in DraftQuiz.model_validate_json(raw).items if (card := quiz_card(item, evidence))]
        else:
            drafts = DraftCards.model_validate_json(raw).items
        if any(card.source > len(evidence) or (not quiz and card.choices) for card in drafts):
            raise ValueError("Invalid choices or source reference.")
    except (ValidationError, ValueError) as error:
        raise HTTPException(422, "The model returned invalid study items. Try a narrower topic or the Balanced model.") from error
    except (httpx.HTTPError, ollama.ResponseError) as error:
        raise HTTPException(503, "The tutor model could not generate study items. Check Local setup.") from error
    if not drafts:
        raise HTTPException(422, "The selected sources did not support any study items for this topic.")
    with database() as db:
        require_course(db, course_id)
        items = []
        for card in drafts:
            row = db.execute("""
                INSERT INTO study_items(course_id,kind,content,evidence,due_at) VALUES (?,?,?,?,?)
                RETURNING *
            """, (course_id, request.kind, card.model_dump_json(exclude={"source"}), json.dumps(evidence[card.source - 1]), int(time()))).fetchone()
            items.append(item_data(row))
        return items


@router.put(BASE + "/{item_id}")
def edit_item(course_id: str, item_id: int, request: PracticeEdit):
    with database() as db:
        item = require_item(db, course_id, item_id)
        if (item["kind"] == "quiz") != bool(request.choices):
            raise HTTPException(422, "A quiz needs choices. A flashcard has a single answer.")
        row = db.execute("""
            UPDATE study_items SET content=?, revision=revision+1
            WHERE id=? AND course_id=? AND revision=? RETURNING *
        """, (request.model_dump_json(exclude={"revision"}), item_id, course_id, request.revision)).fetchone()
        if row is None:
            raise HTTPException(409, "This study item changed. Reopen it and try again.")
        return item_data(row)


@router.post(BASE + "/{item_id}/review")
def review_item(course_id: str, item_id: int, request: Review):
    with database() as db:
        item = require_item(db, course_id, item_id)
        if item["kind"] == "quiz" and request.choice in item["choices"] and request.recalled is None:
            correct = request.choice == item["answer"]
        elif item["kind"] == "flashcard" and request.recalled is not None and request.choice is None:
            correct = request.recalled
        else:
            raise HTTPException(422, "Select a quiz choice or rate your flashcard recall.")
        now = int(time())
        streak = item["streak"] + 1 if correct else 0
        due = now + (min(30, 2 ** min(streak - 1, 5)) * DAY if correct else 600)
        row = db.execute("""
            UPDATE study_items SET streak=?, due_at=?, revision=revision+1
            WHERE id=? AND course_id=? AND revision=? RETURNING *
        """, (streak, due, item_id, course_id, request.revision)).fetchone()
        if row is None:
            raise HTTPException(409, "This study item changed. Reopen it and try again.")
        db.execute("INSERT INTO study_reviews(item_id,reviewed_at,correct) VALUES (?,?,?)", (item_id, now, int(correct)))
        return {"correct": correct, "item": item_data(row)}
