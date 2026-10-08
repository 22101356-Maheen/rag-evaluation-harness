from pydantic_settings import BaseSettings, SettingsConfigDict

# -----------------------------
# Application Settings
# -----------------------------

class Settings(BaseSettings):
    app_name: str = "RAG Evaluation Harness"
    environment: str = "development"

    qdrant_url: str = "http://localhost:6335"

    database_url: str = (
        "postgresql+psycopg://"
        "rag_user:rag_password@localhost:5433/rag_lab"
    )

    clerk_publishable_key: str
    clerk_secret_key: str

    # keep fake auth enabled until the React login flow is connected.
    use_test_auth: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()