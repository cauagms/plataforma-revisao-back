from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.disciplina import Disciplina
from app.models.topico import Topico
from app.models.revisao import Revisao
from app.models.user import User, RoleEnum
from app.schemas.revisao import RevisaoCreate


def _obter_topico_autorizado(
    db: Session, disciplina_id: int, topico_id: int, usuario: User
) -> Topico:
    disciplina = db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
    if not disciplina:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplina não encontrada")
    if usuario.role == RoleEnum.aluno and disciplina.user_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar esta disciplina",
        )
    topico = db.query(Topico).filter(
        Topico.id == topico_id,
        Topico.disciplina_id == disciplina_id,
    ).first()
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado")
    return topico


def criar_revisao(
    db: Session, disciplina_id: int, topico_id: int, dados: RevisaoCreate, usuario: User
) -> Revisao:
    _obter_topico_autorizado(db, disciplina_id, topico_id, usuario)
    revisao = Revisao(
        topico_id=topico_id,
        reflexao=dados.reflexao,
    )
    db.add(revisao)
    db.commit()
    db.refresh(revisao)
    return revisao


def listar_revisoes(
    db: Session, disciplina_id: int, topico_id: int, usuario: User
) -> list[Revisao]:
    _obter_topico_autorizado(db, disciplina_id, topico_id, usuario)
    return (
        db.query(Revisao)
        .filter(Revisao.topico_id == topico_id)
        .order_by(Revisao.criado_em.desc())
        .all()
    )
