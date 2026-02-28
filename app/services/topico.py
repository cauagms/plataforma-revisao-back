from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.disciplina import Disciplina
from app.models.topico import Topico
from app.models.user import User, RoleEnum
from app.schemas.topico import TopicoCreate, TopicoUpdate


def _obter_disciplina_autorizada(db: Session, disciplina_id: int, usuario: User) -> Disciplina:
    disciplina = db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
    if not disciplina:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplina não encontrada")
    if usuario.role == RoleEnum.aluno and disciplina.user_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar esta disciplina",
        )
    return disciplina


def listar_topicos(db: Session, disciplina_id: int, usuario: User) -> list[Topico]:
    _obter_disciplina_autorizada(db, disciplina_id, usuario)
    return db.query(Topico).filter(Topico.disciplina_id == disciplina_id).all()


def obter_topico(db: Session, disciplina_id: int, topico_id: int, usuario: User) -> Topico:
    _obter_disciplina_autorizada(db, disciplina_id, usuario)
    topico = db.query(Topico).filter(
        Topico.id == topico_id,
        Topico.disciplina_id == disciplina_id,
    ).first()
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado")
    return topico


def criar_topico(db: Session, disciplina_id: int, dados: TopicoCreate, usuario: User) -> Topico:
    disciplina = _obter_disciplina_autorizada(db, disciplina_id, usuario)
    topico = Topico(
        titulo=dados.titulo,
        conteudo=dados.conteudo,
        disciplina_id=disciplina.id,
    )
    db.add(topico)
    db.commit()
    db.refresh(topico)
    return topico


def atualizar_topico(
    db: Session, disciplina_id: int, topico_id: int, dados: TopicoUpdate, usuario: User
) -> Topico:
    _obter_disciplina_autorizada(db, disciplina_id, usuario)
    topico = db.query(Topico).filter(
        Topico.id == topico_id,
        Topico.disciplina_id == disciplina_id,
    ).first()
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado")

    if dados.titulo is not None:
        topico.titulo = dados.titulo
    if dados.conteudo is not None:
        topico.conteudo = dados.conteudo

    db.commit()
    db.refresh(topico)
    return topico


def deletar_topico(db: Session, disciplina_id: int, topico_id: int, usuario: User) -> None:
    _obter_disciplina_autorizada(db, disciplina_id, usuario)
    topico = db.query(Topico).filter(
        Topico.id == topico_id,
        Topico.disciplina_id == disciplina_id,
    ).first()
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado")

    db.delete(topico)
    db.commit()
