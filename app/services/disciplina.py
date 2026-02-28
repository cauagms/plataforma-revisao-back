from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.disciplina import Disciplina
from app.models.user import User, RoleEnum
from app.schemas.disciplina import DisciplinaCreate, DisciplinaUpdate


def _verificar_proprietario(disciplina: Disciplina, usuario: User) -> None:
    if disciplina.user_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar esta disciplina",
        )


def listar_disciplinas(db: Session, usuario: User) -> list[Disciplina]:
    if usuario.role == RoleEnum.professor:
        return db.query(Disciplina).all()
    return db.query(Disciplina).filter(Disciplina.user_id == usuario.id).all()


def obter_disciplina(db: Session, disciplina_id: int, usuario: User) -> Disciplina:
    disciplina = db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
    if not disciplina:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplina não encontrada")
    if usuario.role != RoleEnum.professor:
        _verificar_proprietario(disciplina, usuario)
    return disciplina


def criar_disciplina(db: Session, dados: DisciplinaCreate, usuario: User) -> Disciplina:
    disciplina = Disciplina(
        nome=dados.nome,
        descricao=dados.descricao,
        user_id=usuario.id,
    )
    db.add(disciplina)
    db.commit()
    db.refresh(disciplina)
    return disciplina


def atualizar_disciplina(
    db: Session, disciplina_id: int, dados: DisciplinaUpdate, usuario: User
) -> Disciplina:
    disciplina = db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
    if not disciplina:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplina não encontrada")
    _verificar_proprietario(disciplina, usuario)

    if dados.nome is not None:
        disciplina.nome = dados.nome
    if dados.descricao is not None:
        disciplina.descricao = dados.descricao

    db.commit()
    db.refresh(disciplina)
    return disciplina


def deletar_disciplina(db: Session, disciplina_id: int, usuario: User) -> None:
    disciplina = db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
    if not disciplina:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplina não encontrada")
    _verificar_proprietario(disciplina, usuario)

    db.delete(disciplina)
    db.commit()
