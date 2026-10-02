from fastapi import FastAPI

from backend.app.api.routes.evaluation import router as evaluation_router
from backend.app.api.routes.health import router as health_router
from backend.app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0"
)

app.include_router(health_router)
app.include_router(evaluation_router)