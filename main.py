from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.routers import auth, users, disciplinas, topicos, revisoes, estudar_hoje, historico, dashboard
from app.database.connection import engine, Base
import app.models.user  # noqa: F401
import app.models.disciplina  # noqa: F401
import app.models.topico  # noqa: F401
import app.models.revisao  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Plataforma de Revisão Inteligente")

app.state.limiter = auth.limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas requisições. Tente novamente em breve."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(disciplinas.router)
app.include_router(topicos.router)
app.include_router(revisoes.router)
app.include_router(estudar_hoje.router)
app.include_router(historico.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "API Revisão Inteligente rodando!"}