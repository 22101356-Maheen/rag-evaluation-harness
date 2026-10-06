from pydantic_settings import BaseSettings, SettingsConfigDict

# -----------------------------
# Application Settings
# -----------------------------

class Settings(BaseSettings):
    app_name: str = "RAG Evaluation Harness"
    environment: str = "development"

    qdrant_url: str = "http://localhost:6335"

# what this does is it sets the default database URL to a PostgreSQL database running on localhost with the username "rag_user", password "rag_password", and database name "rag_lab". The connection is made using the psycopg driver. This URL can be overridden by setting the DATABASE_URL environment variable in the .env file or in the system environment variables.
    database_url: str = (
        "postgresql+psycopg://"
        "rag_user:rag_password@localhost:5433/rag_lab"
    )

# this is a configuration dictionary for the Settings class. It specifies that the environment variables should be loaded from a file named .env and that the file is encoded in UTF-8. This allows you to easily manage your application's configuration by storing it in a separate .env file, which can be different for each environment (development, testing, production, etc.).
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()