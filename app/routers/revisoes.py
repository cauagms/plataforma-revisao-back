from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.schemas.revisao import RevisaoCreate, RevisaoResponse
from app.services.auth import get_current_user, require_aluno
from app.services import revisao as service

router = APIRouter(
    prefix="/disciplinas/{disciplina_id}/topicos/{topico_id}/revisoes",
    tags=["Revisões"],
)


@router.post("", response_model=RevisaoResponse, status_code=status.HTTP_201_CREATED)
def criar(
    disciplina_id: int,
    topico_id: int,
    dados: RevisaoCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(require_aluno),
):
    return service.criar_revisao(db, disciplina_id, topico_id, dados, usuario)


@router.get("", response_model=list[RevisaoResponse])
def listar(
    disciplina_id: int,
    topico_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return service.listar_revisoes(db, disciplina_id, topico_id, usuario)
