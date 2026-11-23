from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.local_store import database, material_path
from app.models.schemas import CourseCreate, CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])


def require_course(connection, course_id: str):
    course = connection.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("", response_model=CourseResponse, status_code=201)
def create_course(course: CourseCreate):
    record = CourseResponse(id=uuid4().hex, created_at=datetime.now(timezone.utc).isoformat(), **course.model_dump())
    with database() as connection:
        connection.execute("""
            INSERT INTO courses (id, name, color, subject_profile, created_at)
            VALUES (:id, :name, :color, :subject_profile, :created_at)
        """, record.model_dump())
    return record


@router.get("", response_model=list[CourseResponse])
def list_courses():
    with database() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM courses ORDER BY created_at DESC")]


@router.delete("/{course_id}")
def delete_course(course_id: str):
    with database() as connection:
        files = connection.execute("SELECT id FROM materials WHERE course_id=? AND stored_on_disk=1", (course_id,)).fetchall()
        result = connection.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        if not result.rowcount:
            raise HTTPException(status_code=404, detail="Course not found")
    for file in files:
        try:
            material_path(course_id, file["id"]).unlink(missing_ok=True)
        except PermissionError:
            pass
    return {"message": "Course deleted successfully"}
