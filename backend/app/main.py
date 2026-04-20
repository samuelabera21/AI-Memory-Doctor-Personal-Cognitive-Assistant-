from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

from app.config import settings, parse_csv_env
from app.db.database import init_database, engine
from app.services.vector_sync_service import rebuild_faiss_index

from app.api import memory
from app.api import search
from app.api import agent
from app.api import memory_manage
from app.api import auth
from app.api import summarization
from app.api import insight
from app.api import evaluation


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

cors_origins = parse_csv_env(settings.cors_origins)
allowed_hosts = parse_csv_env(settings.allowed_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


@app.on_event("startup")
def startup_event():
    init_database()
    rebuild_faiss_index()


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(memory.router, tags=["memory-write"])
app.include_router(search.router, tags=["memory-search"])
app.include_router(memory_manage.router, tags=["memory-manage"])
app.include_router(summarization.router, tags=["summarization"])
app.include_router(insight.router, tags=["insight"])
app.include_router(agent.router, tags=["agent"])
app.include_router(evaluation.router)


@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running",
        "version": "2.0",
        "environment": settings.environment,
    }


@app.get("/health/live")
def liveness_check():
    return {"status": "alive"}


@app.get("/health/ready")
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        return {
            "status": "not_ready",
            "detail": str(exc),
        }
