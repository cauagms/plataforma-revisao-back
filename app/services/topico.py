from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func
from app.models.disciplina import Disciplina
from app.models.topico import Topico
from app.models.revisao import Revisao
from app.models.user import User, RoleEnum
from app.schemas.topico import TopicoCreate, TopicoUpdate
from app.services.estudar_hoje import classificar_status_revisao


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


def _enriquecer_topico(topico: Topico) -> dict:
    total = len(topico.revisoes)
    ultima = max((r.criado_em for r in topico.revisoes), default=None) if total > 0 else None
    status_revisao, _ = classificar_status_revisao(total, ultima, topico.criado_em)
    if status_revisao is not None:
        if status_revisao.value == "atrasado":
            status = "Atrasado"
        elif status_revisao.value == "primeira_revisao":
            status = "Pendente"
        else:
            status = "Revisar hoje"
    else:
        status = "Revisado" if total > 0 else "Pendente"
    return {
        "id": topico.id,
        "titulo": topico.titulo,
        "conteudo": topico.conteudo,
        "disciplina_id": topico.disciplina_id,
        "criado_em": topico.criado_em,
        "atualizado_em": topico.atualizado_em,
        "status": status,
        "ultima_revisao_em": ultima,
        "total_revisoes": total,
    }


def listar_topicos(db: Session, disciplina_id: int, usuario: User) -> list[dict]:
    _obter_disciplina_autorizada(db, disciplina_id, usuario)
    topicos = (
        db.query(Topico)
        .options(joinedload(Topico.revisoes))
        .filter(Topico.disciplina_id == disciplina_id)
        .all()
    )
    return [_enriquecer_topico(t) for t in topicos]


def obter_topico(db: Session, disciplina_id: int, topico_id: int, usuario: User) -> dict:
    _obter_disciplina_autorizada(db, disciplina_id, usuario)
    topico = (
        db.query(Topico)
        .options(joinedload(Topico.revisoes))
        .filter(Topico.id == topico_id, Topico.disciplina_id == disciplina_id)
        .first()
    )
    if not topico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tópico não encontrado")
    return _enriquecer_topico(topico)


def criar_topico(db: Session, disciplina_id: int, dados: TopicoCreate, usuario: User) -> Topico:
    disciplina = _obter_disciplina_autorizada(db, disciplina_id, usuario)
    agora_utc = datetime.now(timezone.utc)
    topico = Topico(
        titulo=dados.titulo,
        conteudo=dados.conteudo,
        disciplina_id=disciplina.id,
        criado_em=agora_utc,
        atualizado_em=agora_utc,
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
