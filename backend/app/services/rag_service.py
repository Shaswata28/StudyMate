import hashlib
import heapq
import logging
import re
import struct

import httpx

from app.core.config import settings

QUERY_WORDS = re.compile(r"[^\W_]{3,}")
COMMON_WORDS = {"about", "and", "can", "does", "for", "from", "how", "the", "this", "what", "when", "which", "with", "you"}


def passage_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def resolve_passage(connection, course_id, source, question):
    """Resolve saved evidence against current data and reject changed passages."""
    rows = connection.execute("""
        SELECT p.rowid, p.text, m.name FROM material_index p
        JOIN materials m ON m.id=p.material_id
        WHERE m.course_id=? AND m.id=? AND m.processing_status='completed'
          AND (CASE WHEN p.page > 0 THEN p.page ELSE 0 END)=?
        ORDER BY p.rowid
    """, (course_id, source["id"], source.get("page") or 0))
    matches = [
        ({**source, "name": row["name"], "passage_id": row["rowid"]}, row["text"])
        for row in rows
    ] or legacy_context(connection, course_id, question, source["id"])
    fingerprint = source.get("passage_hash")
    matches = [(ref, text) for ref, text in matches if ref.get("page") == source.get("page")]
    if fingerprint:
        return next(((ref, text) for ref, text in matches if passage_fingerprint(text) == fingerprint), None)
    # Older references identify a page, so only resolve when the page has one candidate.
    return matches[0] if len(matches) == 1 else None


def evidence_budget(question: str) -> int:
    return max(0, (settings.LLM_CONTEXT_SIZE - settings.LLM_MAX_RESPONSE_TOKENS - 512) * 2 - len(question.encode()))


def legacy_context(connection, course_id: str, query: str, material_id: str | None = None, *, overview=False):
    words = set(QUERY_WORDS.findall(query.casefold())) - COMMON_WORDS
    if not words and not overview:
        return []

    materials = connection.execute(
        "SELECT id, name, extracted_text FROM materials WHERE course_id = ? AND stored_on_disk=0 AND processing_status='completed' AND (? IS NULL OR id=?)", (course_id, material_id, material_id)
    )
    matches = []
    for material in materials:
        text = material["extracted_text"]
        # Preserve PDF page labels so the tutor can cite the passage.
        for page in re.split(r"(?=^\[Page \d+\]$)", text, flags=re.MULTILINE):
            label, _, body = page.partition("\n")
            if not label.startswith("[Page "):
                label, body = "", page
            for start in range(0, len(body), 800):
                excerpt = body[start:start + 1000].strip()
                score = len(words.intersection(QUERY_WORDS.findall(excerpt.casefold())))
                if excerpt and (score or overview):
                    page_number = int(label[6:-1]) if label else None
                    matches.append((score, {"id": material["id"], "name": material["name"], "page": page_number}, excerpt))
    matches.sort(key=lambda match: match[0], reverse=True)
    return [(source, excerpt) for _, source, excerpt in matches[:3]]


def search_context(connection, course_id: str, query: str, material_id: str | None = None, *, overview=False):
    scope = "m.course_id=? AND m.processing_status='completed'"
    parameters = [course_id]
    if material_id:
        scope += " AND m.id=?"
        parameters.append(material_id)

    words = list(dict.fromkeys(QUERY_WORDS.findall(query.casefold())))[:24]
    terms = " OR ".join(f'"{word}"' for word in words if word not in COMMON_WORDS)
    columns = "p.rowid AS passage_id, m.id, m.name, p.page, p.text"
    join = "FROM material_index p JOIN materials m ON m.id=p.material_id"
    hits = connection.execute(f"""
        SELECT {columns} {join}
        WHERE {scope} AND material_index MATCH ? ORDER BY bm25(material_index) LIMIT 12
    """, [*parameters, terms]).fetchall() if terms else []

    model = settings.EMBEDDING_MODEL
    semantic = []
    vectors = f"""
        SELECT {columns}, v.vector {join} JOIN material_vectors v ON v.passage_id=p.rowid
        WHERE {scope} AND m.embedding_model=?
    """
    if model and connection.execute(f"SELECT 1 FROM ({vectors}) LIMIT 1", [*parameters, model]).fetchone():
        try:
            response = httpx.post(settings.OLLAMA_BASE_URL.rstrip("/") + "/api/embed",
                                  json={"model": model, "input": query}, timeout=8)
            response.raise_for_status()
            vector = response.json()["embeddings"][0]
            unpack = struct.Struct(f"<{len(vector)}f")
            ranked = (
                (sum(a * b for a, b in zip(vector, unpack.unpack(row["vector"]))), row["passage_id"], row)
                for row in connection.execute(vectors, [*parameters, model])
                if vector and len(row["vector"]) == unpack.size
            )
            semantic = [row for score, _, row in heapq.nlargest(12, ranked) if score >= .35]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            logging.getLogger(__name__).warning("Using keyword retrieval because query embedding is unavailable")

    scores = {}
    passages = {}
    for ranking in (hits, semantic):
        for rank, row in enumerate(ranking, start=1):
            key = row["passage_id"]
            scores[key] = scores.get(key, 0) + 1 / (20 + rank)
            passages[key] = row
    rows = [passages[key] for key in sorted(scores, key=scores.get, reverse=True)[:3]]
    if not rows and material_id and overview:
        rows = connection.execute(f"SELECT {columns} {join} WHERE {scope} ORDER BY p.rowid LIMIT 3", parameters).fetchall()
    if not rows:
        return legacy_context(connection, course_id, query, material_id, overview=overview)
    return [
        ({"id": row["id"], "passage_id": row["passage_id"], "name": row["name"], "page": row["page"] if row["page"] > 0 else None}, row["text"])
        for row in rows
    ]
