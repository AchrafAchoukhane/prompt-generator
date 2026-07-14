from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.optimizations import router as optimizations_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="REST API for category-aware prompt analysis and optimization.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(optimizations_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs", "health": f"{settings.api_v1_prefix}/health"}

