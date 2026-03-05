from fastapi import HTTPException, status
from sqlalchemy import func as sql_func
from sqlalchemy.orm import Session
from app.models.disciplina import Disciplina
from app.models.topico import Topico
from app.models.revisao import Revisao
from app.models.user import User, RoleEnum
from app.schemas.disciplina import DisciplinaCreate, DisciplinaUpdate


def _verificar_proprietario(disciplina: Disciplina, usuario: User) -> None:
    if disciplina.user_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar esta disciplina",
        )


def listar_disciplinas(db: Session, usuario: User) -> list[dict]:
    total_sub = (
        db.query(
            Topico.disciplina_id,
            sql_func.count(Topico.id).label("total_topicos"),
        )
        .group_by(Topico.disciplina_id)
        .subquery()
    )

    revisados_sub = (
        db.query(
            Topico.disciplina_id,
            sql_func.count(sql_func.distinct(Topico.id)).label("topicos_revisados"),
        )
        .join(Revisao, Revisao.topico_id == Topico.id)
        .group_by(Topico.disciplina_id)
        .subquery()
    )

    query = (
        db.query(
            Disciplina,
            sql_func.coalesce(total_sub.c.total_topicos, 0).label("total_topicos"),
            sql_func.coalesce(revisados_sub.c.topicos_revisados, 0).label("topicos_revisados"),
        )
        .outerjoin(total_sub, Disciplina.id == total_sub.c.disciplina_id)
        .outerjoin(revisados_sub, Disciplina.id == revisados_sub.c.disciplina_id)
    )

    if usuario.role != RoleEnum.professor:
        query = query.filter(Disciplina.user_id == usuario.id)

    resultados = query.all()

    disciplinas = []
    for disc, total, revisados in resultados:
        d = disc.__dict__.copy()
        d.pop("_sa_instance_state", None)
        d["total_topicos"] = total
        d["topicos_revisados"] = revisados
        d["percentual_revisados"] = round((revisados / total) * 100) if total > 0 else 0
        disciplinas.append(d)

    return disciplinas


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
        cor=dados.cor,
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
    if dados.cor is not None:
        disciplina.cor = dados.cor

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
