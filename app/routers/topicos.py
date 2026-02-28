from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.schemas.topico import TopicoCreate, TopicoUpdate, TopicoResponse
from app.services.auth import get_current_user, require_aluno
from app.services import topico as service

router = APIRouter(prefix="/disciplinas/{disciplina_id}/topicos", tags=["Tópicos"])


@router.get("", response_model=list[TopicoResponse])
def listar(
    disciplina_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return service.listar_topicos(db, disciplina_id, usuario)


@router.post("", response_model=TopicoResponse, status_code=status.HTTP_201_CREATED)
def criar(
    disciplina_id: int,
    dados: TopicoCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(require_aluno),
):
    return service.criar_topico(db, disciplina_id, dados, usuario)


@router.get("/{topico_id}", response_model=TopicoResponse)
def obter(
    disciplina_id: int,
    topico_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return service.obter_topico(db, disciplina_id, topico_id, usuario)


@router.put("/{topico_id}", response_model=TopicoResponse)
def atualizar(
    disciplina_id: int,
    topico_id: int,
    dados: TopicoUpdate,
    db: Session = Depends(get_db),
    usuario: User = Depends(require_aluno),
):
    return service.atualizar_topico(db, disciplina_id, topico_id, dados, usuario)


@router.delete("/{topico_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar(
    disciplina_id: int,
    topico_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(require_aluno),
):
    service.deletar_topico(db, disciplina_id, topico_id, usuario)
