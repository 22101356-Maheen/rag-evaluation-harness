from pydantic import Field, SecretStr
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

    groq_api_key: SecretStr | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"

    generation_model: str = "openai/gpt-oss-20b"
    evaluation_model: str = "openai/gpt-oss-120b"
    synthetic_dataset_model: str = "openai/gpt-oss-20b"

    llm_timeout_seconds: float = Field(default=30, gt=0, le=120)
    llm_context_token_budget: int = Field(default=4000, ge=512, le=16000)
    default_evaluation_case_count: int = Field(default=8, ge=1, le=12)
    evaluation_prompt_version: str = "day9-v1"    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
