from pydantic_settings import BaseSettings, SettingsConfigDict

# -----------------------------
# Application Settings
# -----------------------------

class Settings(BaseSettings):
    app_name: str = "RAG Evaluation Harness"
    environment: str = "development"
    qdrant_url: str = "http://localhost:6335"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()