"""
app/main.py

FastAPI application entry point.

Responsibilities:
- Create the FastAPI application.
- Register middleware (CORS).
- Mount routers.
- Expose health check and root endpoints.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.recovery import router as recovery_router
from app.core.config import (
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    CORS_ORIGINS,
)


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Routers
# ============================================================

app.include_router(
    recovery_router,
    prefix="/api/v1",
)


# ============================================================
# Root / Health
# ============================================================

@app.get("/", tags=["Status"])
def root():
    return {
        "name": APP_NAME,
        "status": "running",
        "version": APP_VERSION,
    }


@app.get("/health", tags=["Status"])
def health():
    return {
        "status": "healthy",
    }