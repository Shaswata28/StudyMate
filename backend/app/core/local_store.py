import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path


def data_directory() -> Path:
    if override := os.getenv("STUDYMATE_DATA_DIR"):
        return Path(override).expanduser()
    if sys.platform == "win32":
        return Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "StudyMate"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "StudyMate"
    return Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "studymate"


@contextmanager
def database():
    folder = data_directory()
    folder.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(folder / "studymate.sqlite3")
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    with database() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                academic TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS local_runtime (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                tutor_model TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                settings TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                subject_profile TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS materials (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                extracted_text TEXT NOT NULL,
                content BLOB NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS materials_course ON materials(course_id);
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
                course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                history TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS history_course ON chat_history(course_id, id);
            CREATE TABLE IF NOT EXISTS diagrams (
                id INTEGER PRIMARY KEY,
                course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                mermaid TEXT NOT NULL,
                sources TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS study_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                kind TEXT NOT NULL CHECK (kind IN ('flashcard', 'quiz')),
                content TEXT NOT NULL,
                evidence TEXT NOT NULL,
                due_at INTEGER NOT NULL,
                streak INTEGER NOT NULL DEFAULT 0,
                revision INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS study_items_due ON study_items(course_id, kind, due_at);
            CREATE TABLE IF NOT EXISTS study_reviews (
                id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL REFERENCES study_items(id) ON DELETE CASCADE,
                reviewed_at INTEGER NOT NULL,
                correct INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bookmarks (
                turn_id INTEGER PRIMARY KEY REFERENCES chat_history(id) ON DELETE CASCADE
            );
        """)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(materials)")}
        for name, definition in {
            "processing_status": "TEXT NOT NULL DEFAULT 'completed'",
            "processing_error": "TEXT",
            "processing_updated_at": "TEXT",
            "stored_on_disk": "INTEGER NOT NULL DEFAULT 0",
            "embedding_model": "TEXT",
        }.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE materials ADD COLUMN {name} {definition}")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS material_pages (
                material_id TEXT NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
                page INTEGER NOT NULL,
                text TEXT NOT NULL,
                PRIMARY KEY (material_id, page)
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS material_index USING fts5(
                material_id UNINDEXED, page UNINDEXED, text
            );
            CREATE TABLE IF NOT EXISTS material_vectors (
                passage_id INTEGER PRIMARY KEY,
                material_id TEXT NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
                vector BLOB NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS delete_material_index AFTER DELETE ON materials BEGIN
                DELETE FROM material_index WHERE material_id = OLD.id;
            END;
        """)


def material_path(course_id: str, material_id: str) -> Path:
    return data_directory() / "courses" / course_id / "materials" / material_id

