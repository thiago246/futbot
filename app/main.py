"""Punto de entrada de la API.

Levantar con:   uvicorn app.main:app --reload --port 8000
Documentación:  http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models 
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.routers import auth, behaviors, club_players, friendlies, leagues, matches, users, ws, squads
from app.core.exceptions import register_exception_handlers
from app.services import behavior_service



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        behavior_service.seed_default_behaviors(db)
    yield

app = FastAPI(title="Futbot API", version="0.1.0", lifespan=lifespan)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError):
    """Mientras algo no esté hecho, el endpoint responde 501 en vez de romperse."""
    return JSONResponse(status_code=501, content={"detail": f"Sin implementar: {exc}"})


for r in (auth, users, club_players, behaviors, leagues, friendlies, matches, squads):
    app.include_router(r.router, prefix=settings.API_PREFIX)

app.include_router(ws.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}