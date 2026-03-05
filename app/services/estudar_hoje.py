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


def obter_estudar_hoje(db: Session, usuario: User) -> dict:
    hoje = datetime.now(MANAUS_TZ).date()

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

        revisado_hoje = any(_to_manaus_date(r.criado_em) == hoje for r in revisoes)
        if revisado_hoje:
            concluidos_hoje += 1

        proxima = calcular_proxima_revisao(total, ultima, topico.criado_em)

        if proxima is None:
            continue

        if total == 0:
            if proxima > hoje:
                continue
            status = StatusRevisao.primeira_revisao
        elif proxima == hoje:
            status = StatusRevisao.revisar_hoje
        elif proxima < hoje:
            status = StatusRevisao.atrasado
        else:
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

    return {
        "resumo": {
            "topicos_para_hoje": atrasados + revisar_hoje + primeira_revisao,
            "atrasados": atrasados,
            "revisar_hoje": revisar_hoje,
            "concluidos_hoje": concluidos_hoje,
        },
        "topicos": pendentes,
    }
