from fastapi import APIRouter
from app.api.v1 import artifacts, chat, courses, materials, practice, profile, study

api_router = APIRouter(prefix="/api")
for router in (profile.router, courses.router, materials.router, chat.router, study.router, artifacts.router, practice.router):
    api_router.include_router(router)
