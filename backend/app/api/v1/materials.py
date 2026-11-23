import re
from urllib.parse import quote
from shutil import disk_usage

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.api.v1.courses import require_course
from app.core.local_store import database, material_path
from app.models.schemas import MaterialResponse

router = APIRouter(tags=["materials"])


@router.post("/courses/{course_id}/materials", response_model=MaterialResponse, status_code=201)
def upload_material(course_id: str, file: UploadFile = File(...)):
    with database() as connection:
        require_course(connection, course_id)
    material_id = uuid4().hex
    path = material_path(course_id, material_id)
    size = 0
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if file.size is not None and file.size > disk_usage(path.parent).free:
            raise HTTPException(status_code=507, detail="There is not enough disk space to save this material.")
        with path.open("xb") as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                target.write(chunk)
        if not size:
            raise HTTPException(status_code=422, detail="The file is empty.")
        material = MaterialResponse(
            id=material_id, course_id=course_id, name=file.filename or "Untitled",
            file_type=file.content_type or "application/octet-stream", file_size=size,
            created_at=datetime.now(timezone.utc).isoformat(), processing_status="queued",
        )
        with database() as connection:
            require_course(connection, course_id)
            connection.execute("""
                INSERT INTO materials (id, course_id, name, file_type, file_size, created_at,
                    extracted_text, content, processing_status, stored_on_disk)
                VALUES (:id,:course_id,:name,:file_type,:file_size,:created_at,'',X'','queued',1)
            """, material.model_dump())
    except OSError as error:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=507, detail="Could not save the upload. Check available disk space.") from error
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return material


@router.get("/courses/{course_id}/materials", response_model=list[MaterialResponse])
def list_materials(course_id: str):
    with database() as connection:
        require_course(connection, course_id)
        rows = connection.execute("""
            SELECT id, course_id, name, file_type, file_size, created_at, processing_status, processing_error
            FROM materials WHERE course_id = ? ORDER BY created_at DESC
        """, (course_id,))
        return [dict(row) for row in rows]


@router.get("/courses/{course_id}/materials/{material_id}")
def preview_material(course_id: str, material_id: str, page: int | None = None):
    with database() as connection:
        row = connection.execute(
            "SELECT name, extracted_text, stored_on_disk, processing_status FROM materials WHERE course_id=? AND id=?",
            (course_id, material_id),
        ).fetchone()
        require_ready_material(row)
        if row["stored_on_disk"]:
            if page is not None:
                result = connection.execute("""
                    SELECT substr(text, 1, 20001) AS excerpt FROM material_pages WHERE material_id=? AND page=?
                """, (material_id, page)).fetchone()
                if result is None:
                    raise HTTPException(status_code=404, detail="This source page is no longer available.")
                text = result["excerpt"]
            else:
                pages = connection.execute("""
                    SELECT page, substr(text, 1, 20001) AS excerpt FROM material_pages
                    WHERE material_id=? ORDER BY abs(page)
                """, (material_id,))
                text = ""
                for item in pages:
                    heading = f"[Page {item['page']}]\n" if item["page"] > 0 else ""
                    text += f"{heading}{item['excerpt']}\n\n"
                    if len(text) > 20000:
                        break
        else:
            text = row["extracted_text"]
            if page is not None:
                match = re.search(rf"^\[Page {page}\][ \t]*\n?(.*?)(?=^\[Page \d+\]$|\Z)", text, re.MULTILINE | re.DOTALL)
                if match is None:
                    raise HTTPException(status_code=404, detail="This source page is no longer available.")
                text = match.group(1).strip()
    return {"name": row["name"], "text": text[:20000], "truncated": len(text) > 20000}


def require_ready_material(row):
    if row is None:
        raise HTTPException(status_code=404, detail="This source is no longer available.")
    if row["processing_status"] != "completed":
        raise HTTPException(status_code=409, detail="This material is not ready. Check its status in Materials.")


@router.post("/materials/{material_id}/retry")
def retry_material(material_id: str):
    with database() as connection:
        changed = connection.execute("""
            UPDATE materials SET processing_status='queued', processing_error=NULL
            WHERE id=? AND processing_status='failed'
        """, (material_id,))
        if not changed.rowcount:
            raise HTTPException(status_code=409, detail="Only failed uploads can be retried.")
    return {"processing_status": "queued"}


@router.get("/courses/{course_id}/materials/{material_id}/file")
def download_material(course_id: str, material_id: str):
    with database() as connection:
        row = connection.execute(
            "SELECT name, stored_on_disk, processing_status FROM materials WHERE course_id=? AND id=?",
            (course_id, material_id),
        ).fetchone()
        require_ready_material(row)
        if row["stored_on_disk"]:
            path = material_path(course_id, material_id)
            if not path.is_file():
                raise HTTPException(status_code=404, detail="The original file is missing.")
            return FileResponse(path, media_type="application/octet-stream", filename=row["name"])
        content = connection.execute("SELECT content FROM materials WHERE id=?", (material_id,)).fetchone()["content"]
    return Response(content, media_type="application/octet-stream", headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + quote(row["name"], safe=""),
    })


@router.delete("/materials/{material_id}")
def delete_material(material_id: str):
    with database() as connection:
        row = connection.execute("DELETE FROM materials WHERE id=? RETURNING course_id, stored_on_disk", (material_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Material not found")
    if row["stored_on_disk"]:
        try:
            material_path(row["course_id"], material_id).unlink(missing_ok=True)
        except PermissionError:
            # A worker can still hold a PDF open on Windows.
            pass
    return {"message": "Material deleted successfully"}
