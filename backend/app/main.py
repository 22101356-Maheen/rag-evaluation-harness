from fastapi import FastAPI

from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.evaluation import router as evaluation_router
from backend.app.api.routes.experiments import router as experiments_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.search import router as search_router
from backend.app.core.config import settings

# -----------------------------
# FastAPI Application
# -----------------------------

app = FastAPI(
    title=settings.app_name,
)


# -----------------------------
# API Routes
# -----------------------------

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(evaluation_router)
app.include_router(experiments_router)