"""Minimal FastAPI app — always starts; DB is best-effort."""

from fastapi import FastAPI

from database import check_database

app = FastAPI(
    title="HostCry FastAPI Health",
    description="Server always runs. Database connects when env is configured.",
    version="1.0.0",
)


@app.get("/")
def root():
    db = check_database()
    return {
        "server": "running",
        "message": "Server is running",
        "database": db,
    }


@app.get("/health")
def health():
    """Lightweight health check for deploy platforms / load balancers."""
    db = check_database()
    return {
        "status": "ok",
        "server": "running",
        "database_connected": db["connected"],
        "database": db,
    }


@app.get("/db")
def db_status():
    """Explicit database probe endpoint."""
    return check_database()
