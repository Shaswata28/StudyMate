import os
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Event, Thread
from urllib.parse import urlsplit

import httpx
import ollama
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.api.v1.study import whisper_available
from app.core.config import settings
from app.core.local_store import database, initialize_database
from app.services.local_setup import (
    MODELS, OLLAMA_ASSETS, ensure_ollama, hardware, install_voice, machine, ollama_autosetup, whisper_paths,
)
from app.services.llm_service import ollama_client
from app.services import kokoro
from app.services.material_indexer import run_queue


class ReadAloudRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000, pattern=r"\S")


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    stop = Event()
    indexer = Thread(target=run_queue, args=(stop,), daemon=True)
    indexer.start()
    try:
        yield
    finally:
        stop.set()
        await run_in_threadpool(indexer.join, 65)


def create_app(web_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="StudyMate Local API", version="1.0.0", lifespan=lifespan)

    @app.middleware("http")
    async def check_local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
            if urlsplit(origin).netloc not in {request.headers.get("host"), "localhost:3000", "127.0.0.1:3000"}:
                return JSONResponse({"detail": "Unrecognized request origin"}, status_code=403)
        return await call_next(request)

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
    app.include_router(api_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "version": app.version}

    @app.get("/api/settings")
    async def local_settings():
        model = settings.tutor_model
        try:
            names = await run_in_threadpool(ensure_ollama)
        except (OSError, RuntimeError):
            names = None
        tag = model if ":" in model.rsplit("/", 1)[-1] else f"{model}:latest"
        status = "unavailable" if names is None else "ready" if tag in names else "missing"
        return {"model": model, "vision_enabled": bool(settings.vision_model), "status": status,
                "whisper_available": whisper_available(), "installed_models": sorted(names or ())}

    @app.get("/api/settings/device")
    def device_settings():
        executable, _ = whisper_paths()
        return {
            **hardware(),
            "models": [{"id": model, "name": name, "size": size} for model, name, size in MODELS],
            "ollama_auto": ollama_autosetup() and machine() in OLLAMA_ASSETS,
            "voice_auto": bool(executable or machine() == ("Windows", "amd64")),
        }

    @app.post("/api/settings/voice")
    async def download_voice():
        try:
            await run_in_threadpool(install_voice)
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except (httpx.HTTPError, OSError) as error:
            raise HTTPException(status_code=503, detail="Voice setup could not finish. Check your connection and disk space.") from error
        return {"status": "ready"}

    @app.post("/api/settings/model")
    async def download_model(model: str | None = None):
        if model is not None and model not in {candidate[0] for candidate in MODELS}:
            raise HTTPException(status_code=422, detail="Choose one of the suggested tutor models.")
        selected = model or settings.tutor_model
        try:
            names = await run_in_threadpool(ensure_ollama, True)
            if names is None:
                raise RuntimeError("Ollama did not start. Start it and try again.")
            tag = selected if ":" in selected.rsplit("/", 1)[-1] else f"{selected}:latest"
            if tag not in names:
                progress = await ollama_client().pull(selected, stream=True)
                async for update in progress:
                    if update.status == "success":
                        break
                else:
                    raise RuntimeError("The model download did not complete.")
            if model:
                with database() as connection:
                    connection.execute("""
                        INSERT INTO local_runtime (id, tutor_model) VALUES (1, ?)
                        ON CONFLICT(id) DO UPDATE SET tutor_model = excluded.tutor_model
                    """, (selected,))
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except (OSError, httpx.HTTPError, ollama.ResponseError) as error:
            raise HTTPException(status_code=503, detail="Setup could not finish. Check your internet connection and disk space.") from error
        return {"status": "ready"}

    @app.get("/api/settings/kokoro")
    def kokoro_status():
        return {
            "supported": machine() in kokoro.ASSETS,
            "installed": kokoro.kokoro_files() is not None,
            "progress": kokoro.install_progress,
        }

    @app.post("/api/settings/kokoro")
    async def download_kokoro():
        try:
            await run_in_threadpool(kokoro.install_kokoro)
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except (OSError, httpx.HTTPError) as error:
            raise HTTPException(status_code=503, detail="Kokoro could not download. Check your connection and disk space.") from error
        return {"installed": True}

    @app.post("/api/speech")
    async def read_aloud(request: ReadAloudRequest):
        try:
            audio = await run_in_threadpool(kokoro.synthesize_kokoro, request.text.strip())
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return Response(audio, media_type="audio/wav")

    if web_root is not None:
        app.mount("/", StaticFiles(directory=web_root, html=True))
    return app


web_root = os.environ.get("STUDYMATE_WEB_ROOT")
app = create_app(Path(web_root) if web_root else None)
