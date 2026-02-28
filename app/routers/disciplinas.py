from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.schemas.disciplina import DisciplinaCreate, DisciplinaUpdate, DisciplinaResponse
from app.services.auth import get_current_user, require_aluno
from app.services import disciplina as service

router = APIRouter(prefix="/disciplinas", tags=["Disciplinas"])


@router.get("", response_model=list[DisciplinaResponse])
def listar(
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return service.listar_disciplinas(db, usuario)


@router.post("", response_model=DisciplinaResponse, status_code=status.HTTP_201_CREATED)
def criar(
    dados: DisciplinaCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(require_aluno),
):
    return service.criar_disciplina(db, dados, usuario)


@router.get("/{disciplina_id}", response_model=DisciplinaResponse)
def obter(
    disciplina_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return service.obter_disciplina(db, disciplina_id, usuario)


@router.put("/{disciplina_id}", response_model=DisciplinaResponse)
def atualizar(
    disciplina_id: int,
    dados: DisciplinaUpdate,
    db: Session = Depends(get_db),
    usuario: User = Depends(require_aluno),
):
    return service.atualizar_disciplina(db, disciplina_id, dados, usuario)


@router.delete("/{disciplina_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar(
    disciplina_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(require_aluno),
):
    service.deletar_disciplina(db, disciplina_id, usuario)
