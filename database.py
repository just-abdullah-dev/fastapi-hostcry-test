"""PostgreSQL helpers — never raise on missing/failed connection."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _env_status() -> dict[str, Any]:
    """Report which DB env vars are present (never expose secret values)."""
    has_url = bool(os.getenv("DATABASE_URL", "").strip())
    host = bool(os.getenv("POSTGRES_HOST", "").strip())
    user = bool(os.getenv("POSTGRES_USER", "").strip())
    password = bool(os.getenv("POSTGRES_PASSWORD", "").strip())
    db = bool(os.getenv("POSTGRES_DB", "").strip())
    port = bool(os.getenv("POSTGRES_PORT", "").strip())

    configured = has_url or (host and user and db)

    return {
        "configured": configured,
        "vars": {
            "DATABASE_URL": has_url,
            "POSTGRES_HOST": host,
            "POSTGRES_PORT": port,
            "POSTGRES_USER": user,
            "POSTGRES_PASSWORD": password,
            "POSTGRES_DB": db,
        },
    }


def _build_dsn() -> str | None:
    """Build a DSN from env. Returns None if nothing usable is configured."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url

    host = os.getenv("POSTGRES_HOST", "").strip()
    user = os.getenv("POSTGRES_USER", "").strip()
    password = os.getenv("POSTGRES_PASSWORD", "")
    db = os.getenv("POSTGRES_DB", "").strip()
    port = os.getenv("POSTGRES_PORT", "5432").strip() or "5432"

    if not host or not user or not db:
        return None

    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{db}"
    )


def check_database() -> dict[str, Any]:
    """
    Attempt a lightweight Postgres connection.

    The API stays up whether this succeeds or fails — useful for
    serverless deploys where the DB may not be wired yet.
    """
    env = _env_status()
    dsn = _build_dsn()

    if not dsn:
        return {
            "connected": False,
            "env_configured": False,
            "status": "env_missing",
            "message": (
                "Env vars missing. Add DATABASE_URL or "
                "POSTGRES_HOST / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB."
            ),
            "env": env,
        }

    try:
        import psycopg

        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return {
            "connected": True,
            "env_configured": True,
            "status": "connected",
            "message": "Env vars present and database connected successfully.",
            "env": env,
        }
    except Exception as exc:  # noqa: BLE001 — report any connect/query failure
        return {
            "connected": False,
            "env_configured": True,
            "status": "env_ok_db_failed",
            "message": f"Env vars present but database not connected: {exc}",
            "env": env,
        }
