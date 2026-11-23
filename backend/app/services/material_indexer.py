import logging
import struct
from threading import Event

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.local_store import database, material_path
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class Interrupted(Exception):
    pass


def update_status(material_id, status, error=None, model=None):
    with database() as connection:
        updated = connection.execute("""
            UPDATE materials SET processing_status=?, processing_error=?, embedding_model=?,
                processing_updated_at=CURRENT_TIMESTAMP WHERE id=?
        """, (status, error, model, material_id))
        if not updated.rowcount:
            raise Interrupted


def process_material(job, stop):
    material_id = job["id"]
    model = settings.EMBEDDING_MODEL
    try:
        with database() as connection:
            connection.execute("DELETE FROM material_pages WHERE material_id=?", (material_id,))
            connection.execute("DELETE FROM material_vectors WHERE material_id=?", (material_id,))
            connection.execute("DELETE FROM material_index WHERE material_id=?", (material_id,))
        found = False
        path = material_path(job["course_id"], material_id)
        for page, text in ocr_service.pages(path, job["name"], job["file_type"]):
            if stop.is_set():
                raise Interrupted
            if not text.strip():
                continue
            found = True
            with database() as connection:
                updated = connection.execute("""
                    UPDATE materials SET processing_updated_at=CURRENT_TIMESTAMP WHERE id=?
                """, (material_id,))
                if not updated.rowcount:
                    raise Interrupted
                connection.execute("INSERT INTO material_pages VALUES (?, ?, ?)", (material_id, page, text))
        if not found:
            raise HTTPException(status_code=422, detail="No readable text found. Upload a searchable file.")
        update_status(material_id, "indexing")
        index_pages(material_id, stop)
        if model:
            update_status(material_id, "embedding")
            embed_material(material_id, model, stop)
        if stop.is_set():
            raise Interrupted
        update_status(material_id, "completed", model=model or None)
    except Interrupted:
        if stop.is_set():
            try:
                update_status(material_id, "queued")
            except Interrupted:
                pass
    except (HTTPException, OSError, httpx.HTTPError, ValueError, RuntimeError, KeyError) as error:
        if isinstance(error, HTTPException):
            detail = error.detail
        elif isinstance(error, httpx.HTTPError):
            detail = f"Embedding is unavailable. Start Ollama, install {model}, and retry."
        else:
            logger.exception("Could not process material %s", material_id)
            detail = "Could not process this file. Check that it is readable and retry."
        try:
            update_status(material_id, "failed", detail)
        except Interrupted:
            pass

    finally:
        with database() as connection:
            exists = connection.execute("SELECT 1 FROM materials WHERE id=?", (material_id,)).fetchone()
        if not exists:
            try:
                material_path(job["course_id"], material_id).unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove the original of deleted material %s", material_id)


def index_pages(material_id, stop):
    with database() as connection:
        pages = connection.execute(
            "SELECT page FROM material_pages WHERE material_id=? ORDER BY abs(page)", (material_id,)
        ).fetchall()
    for item in pages:
        if stop.is_set():
            raise Interrupted
        page = item["page"]
        with database() as connection:
            row = connection.execute(
                "SELECT text FROM material_pages WHERE material_id=? AND page=?", (material_id, page)
            ).fetchone()
            if not row:
                raise Interrupted
            text = row["text"]
            passages = (text[start:start + 900].strip() for start in range(0, len(text), 750))
            updated = connection.execute(
                "UPDATE materials SET processing_updated_at=CURRENT_TIMESTAMP WHERE id=?", (material_id,)
            )
            if not updated.rowcount:
                raise Interrupted
            connection.executemany("INSERT INTO material_index VALUES (?, ?, ?)",
                                   ((material_id, page, passage) for passage in passages if passage))


def embed_material(material_id, model, stop):
    last_id = 0
    with httpx.Client(timeout=60) as client:
        while not stop.is_set():
            with database() as connection:
                rows = connection.execute("""
                    SELECT rowid, text FROM material_index
                    WHERE material_id=? AND rowid>? ORDER BY rowid LIMIT 8
                """, (material_id, last_id)).fetchall()
            if not rows:
                return
            response = client.post(settings.OLLAMA_BASE_URL.rstrip("/") + "/api/embed",
                                   json={"model": model, "input": [row["text"] for row in rows]})
            response.raise_for_status()
            vectors = response.json()["embeddings"]
            if len(vectors) != len(rows) or any(not vector for vector in vectors):
                raise ValueError("Invalid embedding batch")
            with database() as connection:
                update = connection.execute("""
                    UPDATE materials SET processing_updated_at=CURRENT_TIMESTAMP WHERE id=?
                """, (material_id,))
                if not update.rowcount:
                    raise Interrupted
                connection.executemany("INSERT INTO material_vectors VALUES (?, ?, ?)", [
                    (row["rowid"], material_id, struct.pack(f"<{len(vector)}f", *vector))
                    for row, vector in zip(rows, vectors)
                ])
            last_id = rows[-1]["rowid"]
    raise Interrupted


def run_queue(stop: Event):
    while not stop.is_set():
        try:
            with database() as connection:
                # Expire a claim if the previous process stopped without shutting down cleanly.
                connection.execute("""
                    UPDATE materials SET processing_status='queued'
                    WHERE processing_status IN ('extracting', 'indexing', 'embedding')
                    AND processing_updated_at < datetime('now', '-3 minutes')
                """)
                job = connection.execute("""
                    UPDATE materials SET processing_status='extracting', processing_updated_at=CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id FROM materials WHERE processing_status='queued'
                        AND NOT EXISTS (
                            SELECT 1 FROM materials WHERE processing_status IN ('extracting','indexing','embedding')
                        )
                        ORDER BY created_at, id LIMIT 1
                    )
                    RETURNING id, course_id, name, file_type
                """).fetchone()
            if job:
                process_material(job, stop)
                continue
        except Exception:
            logger.exception("Material queue failed")
        stop.wait(.4)
