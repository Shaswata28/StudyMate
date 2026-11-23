import json
from pathlib import Path
from subprocess import DEVNULL, TimeoutExpired, run
from tempfile import TemporaryDirectory
from time import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.local_setup import whisper_paths
from app.core.local_store import database

router = APIRouter()


def whisper_available():
    executable, model = whisper_paths()
    return bool(executable and model.is_file())


@router.get("/study")
def study_summary(due_before: int | None = None):
    with database() as connection:
        counts = connection.execute("""
            SELECT (SELECT count(*) FROM courses) AS courses,
                   (SELECT count(*) FROM materials) AS materials,
                   (SELECT count(*) FROM chat_history) AS turns
        """).fetchone()
        rows = connection.execute("""
            SELECT h.id, h.course_id, h.history, h.created_at, c.name
            FROM chat_history h JOIN courses c ON c.id = h.course_id ORDER BY h.id DESC LIMIT 6
        """)
        due_rows = connection.execute("""
            SELECT course_id, count(*) AS count FROM study_items
            WHERE kind='flashcard' AND due_at < ? GROUP BY course_id ORDER BY count DESC, course_id
        """, (due_before if due_before is not None else int(time()) + 1,)).fetchall()
        return {
            **dict(counts),
            "due_flashcards": sum(row["count"] for row in due_rows),
            "due_courses": [dict(row) for row in due_rows],
            "recent": [
                {"id": row["id"], "course_id": row["course_id"], "course": row["name"],
                 "question": json.loads(row["history"])[0]["content"], "created_at": row["created_at"]}
                for row in rows
            ],
        }


@router.post("/transcribe")
def transcribe(audio: UploadFile = File(...)):
    if not whisper_available():
        raise HTTPException(status_code=503, detail="Configure whisper.cpp and a local speech model in Settings.")
    executable, model = whisper_paths()
    content = audio.file.read(2_000_001)
    if len(content) > 2_000_000 or content[:4] != b"RIFF" or content[8:12] != b"WAVE":
        raise HTTPException(status_code=422, detail="Record up to one minute of WAV audio.")
    with TemporaryDirectory() as folder:
        recording = Path(folder) / "speech.wav"
        recording.write_bytes(content)
        transcript = Path(folder) / "transcript"
        try:
            result = run(
                [str(executable), "-m", str(model.resolve()),
                 "-f", str(recording), "-nt", "-np", "-otxt", "-of", str(transcript)],
                stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, timeout=60,
            )
        except (OSError, TimeoutExpired) as error:
            raise HTTPException(status_code=503, detail="Local transcription could not complete.") from error
        output = transcript.with_suffix(".txt")
        if result.returncode or not output.is_file():
            raise HTTPException(status_code=503, detail="Whisper could not read the recording. Check the local model.")
        return {"text": output.read_text(encoding="utf-8", errors="replace").strip()}
