import json

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.local_store import database
from app.models.schemas import LocalProfile, UserPreferences

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=LocalProfile | None)
def get_profile():
    with database() as connection:
        row = connection.execute("SELECT name, academic FROM profile WHERE id = 1").fetchone()
    if row is None:
        return None
    data = json.loads(row["academic"])
    details = data.pop("profile_details", {})
    return LocalProfile(name=row["name"], academic=data, **details)


class ProfileSettings(BaseModel):
    profile: LocalProfile
    prefs: UserPreferences


def write_profile(connection, profile: LocalProfile):
    data = profile.academic.model_dump()
    data["profile_details"] = profile.model_dump(exclude={"name", "academic"})
    connection.execute("""
        INSERT INTO profile (id, name, academic) VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET name = excluded.name, academic = excluded.academic
    """, (profile.name, json.dumps(data, ensure_ascii=False)))


def write_preferences(connection, preferences: UserPreferences):
    connection.execute("""
        INSERT INTO preferences (id, settings) VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET settings = excluded.settings
    """, (preferences.model_dump_json(),))


@router.put("", response_model=LocalProfile)
def save_profile(profile: LocalProfile):
    with database() as connection:
        write_profile(connection, profile)
    return profile


@router.put("/settings", response_model=ProfileSettings)
def save_settings(settings: ProfileSettings):
    with database() as connection:
        write_profile(connection, settings.profile)
        write_preferences(connection, settings.prefs)
    return settings


@router.get("/preferences")
def get_preferences():
    with database() as connection:
        row = connection.execute("SELECT settings FROM preferences WHERE id = 1").fetchone()
    return {"prefs": json.loads(row["settings"]) if row else {}}


@router.post("/preferences")
def save_preferences(preferences: UserPreferences):
    with database() as connection:
        write_preferences(connection, preferences)
    return {"prefs": preferences.model_dump()}
