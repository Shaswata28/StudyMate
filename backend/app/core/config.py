from pydantic import PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    LLM_CORE_MODEL: str = "qwen3.5:0.8b-q8_0"
    LLM_VISION_MODEL: str = ""
    LLM_CONTEXT_SIZE: PositiveInt = 4096
    LLM_MAX_RESPONSE_TOKENS: PositiveInt = 768
    EMBEDDING_MODEL: str = ""
    WHISPER_EXECUTABLE: str = "whisper-cli"
    WHISPER_MODEL: str = ""

    @property
    def tutor_model(self) -> str:
        from app.core.local_store import database

        with database() as connection:
            selected = connection.execute("SELECT tutor_model FROM local_runtime WHERE id = 1").fetchone()
        return selected["tutor_model"] if selected else self.LLM_CORE_MODEL

    @property
    def vision_model(self) -> str:
        if self.LLM_VISION_MODEL:
            return self.LLM_VISION_MODEL
        model = self.tutor_model
        return model if model.startswith("qwen3.5:") else ""


settings = Settings()
