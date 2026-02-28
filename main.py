from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.routers import auth, disciplinas, topicos
from app.database.connection import engine, Base
import app.models.user  # noqa: F401
import app.models.disciplina  # noqa: F401
import app.models.topico  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Plataforma de Revisão Inteligente")

app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(disciplinas.router)
app.include_router(topicos.router)

@app.get("/")
def root():
    return {"message": "API Revisão Inteligente rodando!"}