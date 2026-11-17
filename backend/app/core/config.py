"""
app/core/config.py

Centralised application configuration.

All configurable values are read from environment variables.
Sensitive values (API keys) must never be hardcoded here.
"""
from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# LLM provider
# ============================================================

# Valid values: "mock" | "nvidia"
# Default: "mock" so the app works without any credentials.
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").lower()


# ============================================================
# CORS
# ============================================================

# Origins that the browser is allowed to access.
# Always include the Vite dev server.
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # fallback
]

# Allow origins from env variable (space-separated).
_extra_origins: str = os.getenv("CORS_ORIGINS", "")
if _extra_origins:
    CORS_ORIGINS += [
        o.strip()
        for o in _extra_origins.split(",")
        if o.strip()
    ]


# ============================================================
# Application metadata
# ============================================================

APP_NAME = "ReviveAI"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-powered payment recovery decision system"
