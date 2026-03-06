from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, joinedload

from app.models.disciplina import Disciplina
from app.models.topico import Topico
from app.models.user import RoleEnum, User
from app.schemas.estudar_hoje import StatusRevisao

INTERVALOS_REVISAO = [1, 3, 7, 15, 30]
try:
    MANAUS_TZ = ZoneInfo("America/Manaus")
except Exception:
    MANAUS_TZ = timezone(timedelta(hours=-4))
UTC_TZ = timezone.utc


def _to_manaus_date(dt: datetime | None) -> date | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(MANAUS_TZ).date()


def _to_manaus_datetime(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(MANAUS_TZ)


def calcular_proxima_revisao(
    total_revisoes: int,
    ultima_revisao: datetime | None,
    criado_em: datetime | None = None,
) -> date | None:
    if total_revisoes == 0:
        base = _to_manaus_date(criado_em)
        if base is None:
            return None
    else:
        base = _to_manaus_date(ultima_revisao)
        if base is None:
            return None
    idx = min(total_revisoes, len(INTERVALOS_REVISAO) - 1)
    return base + timedelta(days=INTERVALOS_REVISAO[idx])


def calcular_primeira_revisao_em(criado_em: datetime | None) -> datetime | None:
    criado = _to_manaus_datetime(criado_em)
    if criado is None:
        return None
    return criado + timedelta(days=INTERVALOS_REVISAO[0])


def classificar_status_revisao(
    total_revisoes: int,
    ultima_revisao: datetime | None,
    criado_em: datetime | None,
    agora: datetime | None = None,
) -> tuple[StatusRevisao | None, date | None]:
    agora_manaus = agora.astimezone(MANAUS_TZ) if agora is not None else datetime.now(MANAUS_TZ)
    hoje = agora_manaus.date()

    if total_revisoes == 0:
        primeira_revisao_em = calcular_primeira_revisao_em(criado_em)
        if primeira_revisao_em is None:
            return None, None
        if agora_manaus >= primeira_revisao_em:
            return StatusRevisao.atrasado, primeira_revisao_em.date()
        return StatusRevisao.primeira_revisao, primeira_revisao_em.date()

    proxima = calcular_proxima_revisao(total_revisoes, ultima_revisao, criado_em)
    if proxima is None:
        return None, None
    if proxima < hoje:
        return StatusRevisao.atrasado, proxima
    if proxima == hoje:
        return StatusRevisao.revisar_hoje, proxima
    return None, proxima


def obter_estudar_hoje(db: Session, usuario: User) -> dict:
    agora = datetime.now(MANAUS_TZ)
    hoje = agora.date()

    query = (
        db.query(Topico)
        .join(Topico.disciplina)
        .options(
            joinedload(Topico.disciplina),
            joinedload(Topico.revisoes),
        )
    )

    if usuario.role == RoleEnum.aluno:
        query = query.filter(Disciplina.user_id == usuario.id)

    topicos = query.all()

    pendentes = []
    concluidos_hoje = 0

    for topico in topicos:
        revisoes = topico.revisoes
        total = len(revisoes)
        ultima = max((r.criado_em for r in revisoes), default=None) if total > 0 else None

        concluidos_hoje += sum(1 for r in revisoes if _to_manaus_date(r.criado_em) == hoje)

        status, proxima = classificar_status_revisao(total, ultima, topico.criado_em, agora)
        if status is None or proxima is None:
            continue

        pendentes.append(
            {
                "disciplina_id": topico.disciplina_id,
                "topico_id": topico.id,
                "topico": topico.titulo,
                "disciplina": topico.disciplina.nome,
                "cor_disciplina": topico.disciplina.cor,
                "status": status,
                "ultima_revisao_em": ultima,
                "proxima_revisao_em": proxima,
                "total_revisoes": total,
            }
        )

    atrasados = sum(1 for t in pendentes if t["status"] == StatusRevisao.atrasado)
    revisar_hoje = sum(1 for t in pendentes if t["status"] == StatusRevisao.revisar_hoje)
    primeira_revisao = sum(1 for t in pendentes if t["status"] == StatusRevisao.primeira_revisao)
    revisar_hoje_card = revisar_hoje + primeira_revisao

    return {
        "resumo": {
            "topicos_para_hoje": atrasados + revisar_hoje + primeira_revisao,
            "pendentes": primeira_revisao,
            "atrasados": atrasados,
            "revisar_hoje": revisar_hoje_card,
            "concluidos_hoje": concluidos_hoje,
        },
        "topicos": pendentes,
    }
