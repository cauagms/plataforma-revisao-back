from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User, RoleEnum
from app.services.auth import get_current_user
from app.services import dashboard as service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/visao-geral")
def visao_geral(
    periodo: str = Query("30dias"),
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    if usuario.role != RoleEnum.professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas professores podem acessar o dashboard",
        )
    return service.obter_visao_geral(db, periodo)


@router.get("/atividade-recente")
def atividade_recente(
    periodo: str = Query("30dias"),
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    if usuario.role != RoleEnum.professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas professores podem acessar o dashboard",
        )
    return service.obter_atividade_recente(db, periodo)


@router.get("/revisoes-pendentes")
def revisoes_pendentes(
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    if usuario.role != RoleEnum.professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas professores podem acessar o dashboard",
        )
    return service.obter_revisoes_pendentes(db)


@router.get("/aluno/{aluno_id}/pendencias")
def pendencias_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    if usuario.role != RoleEnum.professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas professores podem acessar o dashboard",
        )
    resultado = service.obter_pendencias_aluno(db, aluno_id)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado",
        )
    return resultado
