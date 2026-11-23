import json
import re
import logging
from base64 import b64decode
from binascii import Error
from datetime import datetime, timezone

import httpx
import ollama
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.v1.courses import require_course
from app.core.config import settings
from app.core.local_store import database
from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm_service import generate_chat
from app.services.prompt_service import prompt_service
from app.services.rag_service import evidence_budget, passage_fingerprint, search_context

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])
BARE_FOLLOW_UP = re.compile(r"\s*(?:explain|diagram|summarize|describe) (?:that|it)[.!?]?\s*", re.I)
CLARIFICATION_PREFIX = "Which should I focus on:"
DIAGRAM_REQUEST = re.compile(
    r"\b(?:draw|show|generate|create|make|give|sketch)\b[^.!?\n]{0,75}\b(?:diagram|digram|flowchart)\b"
    r"|^\s*(?:diagram|flowchart|digram)\b",
    re.I,
)


def measurement_reply(question: str, passages: list[str]) -> str | None:
    """Quote evidence directly for measurement lookups and explicit reversals."""
    question = re.sub(r"\?\s*(?:cite the (?:excerpt|source)\.?\s*)?$", "", question.strip(), flags=re.I)
    directional = re.fullmatch(r"why did (?:the )?(.+?) (gain|lose) (.+)", question, re.I)
    lookup = re.fullmatch(r"what (?:is|was) (?:the )?(.+?)[’']s measured (.+?)(?: and its (.+))?", question, re.I)
    if not directional and not lookup:
        return None
    subject, operation, detail = (directional or lookup).groups()
    for index, passage in enumerate(passages, start=1):
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", passage):
            lower = sentence.casefold()
            quantity = detail if directional else operation
            if subject.casefold() not in lower or quantity.casefold() not in lower or not re.search(r"\d", sentence):
                continue
            if directional:
                opposite = r"\b(?:decreased|dropped|fell)\b" if operation.lower() == "gain" else r"\b(?:increased|rose|grew)\b"
                if not re.search(rf"{re.escape(quantity.casefold())}\s+{opposite}", lower):
                    continue
                return f"The source reports the opposite change. [Source {index}]\n\n> {sentence.strip()}"
            if detail and any(re.search(rf"\b{re.escape(detail.casefold())}\b", item.casefold()) for item in passages):
                return None
            reply = f"The source reports this measurement. [Source {index}]\n\n> {sentence.strip()}"
            if detail:
                reply += f"\n\nThe retrieved passages do not report its {detail}."
            return reply
    return None


def prepare_turn(course_id: str, question: str, material_id: str | None = None, *, allow_direct_reply=False):
    with database() as connection:
        course = require_course(connection, course_id)
        turns = connection.execute("""
            SELECT history FROM chat_history WHERE course_id = ? ORDER BY id DESC LIMIT 3
        """, (course_id,)).fetchall()
        # Use the saved style to start a course conversation. Follow-ups use its recent turns.
        profile = None
        preferences = None
        if not turns:
            profile = connection.execute("SELECT academic FROM profile WHERE id = 1").fetchone()
            preferences = connection.execute("SELECT settings FROM preferences WHERE id = 1").fetchone()
        if material_id:
            material = connection.execute(
                "SELECT processing_status FROM materials WHERE id = ? AND course_id = ?",
                (material_id, course_id),
            ).fetchone()
            if material is None:
                raise HTTPException(status_code=404, detail="Attached material was not found in this course.")
            if material["processing_status"] != "completed":
                raise HTTPException(status_code=409, detail="This material is still being processed. Check Materials for its status.")
        history = [message for turn in reversed(turns) for message in json.loads(turn["history"])]
        bare_follow_up = BARE_FOLLOW_UP.fullmatch(question)
        if allow_direct_reply and not material_id and len(history) >= 2 and bare_follow_up:
            comparison = re.fullmatch(
                r"\s*compare (.+?) (?:and|with|versus) ([^.!?]+)[.!?]?\s*",
                history[-2]["content"], re.I,
            )
            if comparison:
                first, second = comparison.groups()
                return "", [], [], f"{CLARIFICATION_PREFIX} {first.strip()} or {second.strip()}?"
        # Carry the previous topic only for explicit references, keeping file scope authoritative.
        follow_up = bare_follow_up or re.search(r"\b(?:that|those)(?=[?.!,;]|$)|\b(?:them|the (?:first|second|previous) (?:one|method|example))\b", question, re.I)
        parts = re.split(r"\n\s*\d+[.)]\s+|\s*;\s*|\s+and\s+(?=(?:explain|compare|diagram|summarize|identify|evaluate)\b)", question, flags=re.I)
        excerpts = {}
        parts = [part for part in parts if part.strip()]
        for index, part in enumerate(parts[:3], start=1):
            query = part
            if follow_up and history:
                previous_sources = history[-1].get("sources", [])
                if not material_id or any(source["id"] == material_id for source in previous_sources):
                    query = f"{part} {history[-2]['content'][:500]}"
            overview = bool(re.match(r"\s*(?:(?:explain|summarize) (?:this|the) (?:file|document|material|attachment)\s*[.!?]?\s*$|give (?:me )?an overview)", part, re.I))
            matches = search_context(connection, course_id, query, material_id, overview=overview)
            if follow_up and query != part:
                previous_passages = {
                    (source["id"], source.get("passage_hash")) for source in previous_sources
                }
                matches.sort(key=lambda match: (
                    match[0]["id"], passage_fingerprint(match[1])
                ) not in previous_passages)
            for source, excerpt in matches[:2 if len(parts) > 1 else 3]:
                fingerprint = passage_fingerprint(excerpt)
                key = (source["id"], source["page"], fingerprint)
                if key not in excerpts:
                    excerpts[key] = ({**source, "passage_hash": fingerprint}, excerpt, [])
                excerpts[key][2].append(index)

    sources = []
    passages = []
    context_blocks = []
    # Leave room for the full question, tutor instructions, and the answer.
    remaining = evidence_budget(question)
    covered = set()
    for source, excerpt, part_numbers in excerpts.values():
        page = f", page {source['page']}" if source["page"] else ""
        label = f"Source {len(sources) + 1}: {source['name']}{page}"
        if len(parts) > 1:
            label += " (requested parts " + ", ".join(map(str, part_numbers)) + ")"
        block = f"{label}\n{excerpt}"
        size = len(block.encode())
        if size <= remaining:
            context_blocks.append(block)
            sources.append(source)
            passages.append(excerpt)
            covered.update(part_numbers)
            remaining -= size
    context = "\n\n".join(context_blocks)
    if len(parts) > 1:
        part_summary = "\n".join(
            f"{index}. {part.strip()[:120]}{' (no matching passage supplied)' if index not in covered else ''}"
            for index, part in enumerate(parts[:3], start=1)
        )
        context += "\nRequested parts in order:\n" + part_summary
    if material_id:
        context += "\nAnswer from the selected file. If the excerpts do not establish something, say it could not be found in the file."
    history_budget = remaining
    kept = []
    for index in range(len(history) - 2, -1, -2):
        limit = 700 if not kept else 300
        pair = [{**msg, "content": msg["content"][:limit]} for msg in history[index:index + 2]]
        size = sum(len(msg["content"].encode()) for msg in pair)
        if size > history_budget:
            break
        kept[0:0] = pair
        history_budget -= size
    history = kept
    system_prompt = prompt_service.build_system_prompt(
        academic_profile=json.loads(profile["academic"]) if profile else None,
        preferences=json.loads(preferences["settings"]) if preferences else None,
        context=context,
        subject_profile=course["subject_profile"],
        source_only=bool(material_id),
        diagram_request=bool(DIAGRAM_REQUEST.search(question)),
    )
    return system_prompt, history, sources, measurement_reply(question, passages) if allow_direct_reply else None


@router.post("/courses/{course_id}/chat", response_model=ChatResponse, status_code=201)
async def course_chat(course_id: str, request: ChatRequest):
    images = []
    for attachment in request.attachments:
        if attachment.mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=422, detail="Attach a PNG, JPEG, or WebP image.")
        if not settings.vision_model:
            raise HTTPException(status_code=422, detail="Image chat requires an optional vision model.")
        try:
            images.append(b64decode(attachment.data, validate=True))
        except Error as error:
            raise HTTPException(status_code=422, detail="Invalid image attachment.") from error

    system_prompt, history, sources, direct_reply = await run_in_threadpool(
        prepare_turn, course_id, request.message, request.material_id, allow_direct_reply=not images
    )
    try:
        if direct_reply:
            reply = direct_reply
        elif request.material_id and not sources and not images:
            reply = "I couldn't find a passage in the selected file that answers this question."
        elif not images and DIAGRAM_REQUEST.search(request.message) and not re.search(
            r"\b(?:sequence diagram|branch(?:es|ing)?|mermaid (?:code|syntax))\b", request.message, re.I
        ):
            reply = await generate_chat(system_prompt, history, request.message, images, flowchart=True)
        else:
            reply = await generate_chat(system_prompt, history, request.message, images)
    except ollama.ResponseError as error:
        if error.status_code == 404:
            model = settings.vision_model if images else settings.tutor_model
            raise HTTPException(status_code=503, detail=f"Install the model with: ollama pull {model}") from error
        logger.exception("Ollama generation failed")
        raise HTTPException(status_code=503, detail="The local model could not answer. Check Ollama.") from error
    except (ConnectionError, httpx.RequestError) as error:
        raise HTTPException(status_code=503, detail="Start Ollama on this computer and try again.") from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    reply = re.sub(r"\[Source (\d+)\]", lambda match: match[0] if 0 < int(match[1]) <= len(sources) else "[source unavailable]", reply, flags=re.I)
    timestamp = datetime.now(timezone.utc).isoformat()
    turn = [{"role": "user", "content": request.message}, {"role": "model", "content": reply, "sources": sources}]
    with database() as connection:
        require_course(connection, course_id)
        saved = connection.execute(
            "INSERT INTO chat_history (course_id, history, created_at) VALUES (?, ?, ?) RETURNING id",
            (course_id, json.dumps(turn, ensure_ascii=False), timestamp),
        ).fetchone()
    return ChatResponse(id=saved["id"], response=reply, timestamp=timestamp)


@router.get("/courses/{course_id}/chat")
def get_course_chat_history(course_id: str):
    with database() as connection:
        require_course(connection, course_id)
        rows = connection.execute("""
            SELECT h.*, b.turn_id IS NOT NULL AS bookmarked
            FROM chat_history h LEFT JOIN bookmarks b ON b.turn_id = h.id
            WHERE h.course_id = ? ORDER BY h.id
        """, (course_id,))
        return [{**dict(row), "history": json.loads(row["history"])} for row in rows]


@router.put("/courses/{course_id}/chat/{turn_id}/bookmark")
def set_bookmark(course_id: str, turn_id: int, saved: bool):
    with database() as connection:
        exists = connection.execute(
            "SELECT 1 FROM chat_history WHERE course_id = ? AND id = ?", (course_id, turn_id)
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Answer not found in this course.")
        if saved:
            connection.execute("INSERT OR IGNORE INTO bookmarks (turn_id) VALUES (?)", (turn_id,))
        else:
            connection.execute("DELETE FROM bookmarks WHERE turn_id = ?", (turn_id,))
    return {"bookmarked": saved}
