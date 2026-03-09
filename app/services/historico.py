from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func as sql_func
from sqlalchemy.orm import Session, joinedload

from app.models.disciplina import Disciplina
from app.models.revisao import Revisao
from app.models.topico import Topico
from app.models.user import RoleEnum, User

try:
    MANAUS_TZ = ZoneInfo("America/Manaus")
except Exception:
    MANAUS_TZ = timezone(timedelta(hours=-4))
UTC_TZ = timezone.utc


def _to_manaus_datetime(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(MANAUS_TZ)


def _calcular_inicio_periodo(periodo: str | None, hoje: date, data_inicio: str | None, data_fim: str | None) -> tuple[datetime | None, datetime | None]:
    if periodo == "hoje":
        inicio = datetime(hoje.year, hoje.month, hoje.day, tzinfo=MANAUS_TZ)
        fim = inicio + timedelta(days=1)
        return inicio, fim

    if periodo == "7dias":
        inicio = datetime(hoje.year, hoje.month, hoje.day, tzinfo=MANAUS_TZ) - timedelta(days=6)
        fim = datetime(hoje.year, hoje.month, hoje.day, tzinfo=MANAUS_TZ) + timedelta(days=1)
        return inicio, fim

    if periodo == "30dias":
        inicio = datetime(hoje.year, hoje.month, hoje.day, tzinfo=MANAUS_TZ) - timedelta(days=29)
        fim = datetime(hoje.year, hoje.month, hoje.day, tzinfo=MANAUS_TZ) + timedelta(days=1)
        return inicio, fim

    if periodo == "personalizado" and data_inicio and data_fim:
        dt_inicio = date.fromisoformat(data_inicio)
        dt_fim = date.fromisoformat(data_fim)
        inicio = datetime(dt_inicio.year, dt_inicio.month, dt_inicio.day, tzinfo=MANAUS_TZ)
        fim = datetime(dt_fim.year, dt_fim.month, dt_fim.day, tzinfo=MANAUS_TZ) + timedelta(days=1)
        return inicio, fim

    return None, None


def _inicio_semana_manaus(hoje: date) -> datetime:
    dias_desde_segunda = hoje.weekday()
    segunda = hoje - timedelta(days=dias_desde_segunda)
    return datetime(segunda.year, segunda.month, segunda.day, tzinfo=MANAUS_TZ)


def obter_historico(
    db: Session,
    usuario: User,
    disciplina_id: int | None = None,
    periodo: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> dict:
    agora = datetime.now(MANAUS_TZ)
    hoje = agora.date()

    query = (
        db.query(Revisao)
        .join(Revisao.topico)
        .join(Topico.disciplina)
        .options(
            joinedload(Revisao.topico).joinedload(Topico.disciplina),
        )
    )

    if usuario.role == RoleEnum.aluno:
        query = query.filter(Disciplina.user_id == usuario.id)

    if disciplina_id is not None:
        query = query.filter(Topico.disciplina_id == disciplina_id)

    inicio_periodo, fim_periodo = _calcular_inicio_periodo(periodo, hoje, data_inicio, data_fim)
    if inicio_periodo is not None and fim_periodo is not None:
        query = query.filter(
            Revisao.criado_em >= inicio_periodo.astimezone(UTC_TZ),
            Revisao.criado_em < fim_periodo.astimezone(UTC_TZ),
        )

    revisoes = query.order_by(Revisao.criado_em.desc()).all()

    # Resumo
    total_revisoes = len(revisoes)

    inicio_semana = _inicio_semana_manaus(hoje)
    revisoes_semana = sum(
        1 for r in revisoes
        if _to_manaus_datetime(r.criado_em) is not None
        and _to_manaus_datetime(r.criado_em) >= inicio_semana
    )

    disciplinas_ids = set()
    ultima_revisao_dt = None
    for r in revisoes:
        disciplinas_ids.add(r.topico.disciplina_id)
        if ultima_revisao_dt is None or (r.criado_em and r.criado_em > ultima_revisao_dt):
            ultima_revisao_dt = r.criado_em

    lista_revisoes = []
    for r in revisoes:
        lista_revisoes.append({
            "id": r.id,
            "topico_id": r.topico_id,
            "topico": r.topico.titulo,
            "disciplina_id": r.topico.disciplina_id,
            "disciplina": r.topico.disciplina.nome,
            "cor_disciplina": r.topico.disciplina.cor,
            "reflexao": r.reflexao,
            "criado_em": _to_manaus_datetime(r.criado_em),
        })

    return {
        "resumo": {
            "total_revisoes": total_revisoes,
            "revisoes_semana": revisoes_semana,
            "disciplinas_revisadas": len(disciplinas_ids),
            "ultima_revisao": _to_manaus_datetime(ultima_revisao_dt),
        },
        "revisoes": lista_revisoes,
    }
