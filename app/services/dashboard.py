from datetime import datetime, timedelta

from sqlalchemy import func as sql_func
from sqlalchemy.orm import Session, joinedload

from app.models.user import User, RoleEnum
from app.models.disciplina import Disciplina
from app.models.topico import Topico
from app.models.revisao import Revisao
from app.services.estudar_hoje import (
    calcular_proxima_revisao,
    classificar_status_revisao,
    _to_manaus_date,
    MANAUS_TZ,
)


CORES_AVATAR = [
    "#10b981", "#8b5cf6", "#06b6d4", "#f43f5e",
    "#f59e0b", "#3b82f6", "#ec4899", "#14b8a6",
    "#a855f7", "#ef4444", "#6366f1", "#84cc16",
]


def _iniciais(nome: str) -> str:
    partes = nome.strip().split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[-1][0]).upper()
    return partes[0][0].upper() if partes else "?"


def _cor_avatar(user_id: int) -> str:
    return CORES_AVATAR[user_id % len(CORES_AVATAR)]


def _calcular_inicio_periodo(periodo: str, agora: datetime) -> datetime:
    if periodo == "7dias":
        return agora - timedelta(days=7)
    if periodo == "mes":
        return agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return agora - timedelta(days=30)


def obter_visao_geral(db: Session, periodo: str = "30dias") -> dict:
    alunos = db.query(User).filter(User.role == RoleEnum.aluno).all()

    agora = datetime.now(MANAUS_TZ)
    inicio = _calcular_inicio_periodo(periodo, agora)

    total_revisoes_geral = 0
    total_pendentes_geral = 0
    alunos_desempenho = []

    todos_topicos = (
        db.query(Topico)
        .join(Disciplina, Disciplina.id == Topico.disciplina_id)
        .join(User, User.id == Disciplina.user_id)
        .filter(User.role == RoleEnum.aluno)
        .options(
            joinedload(Topico.disciplina),
            joinedload(Topico.revisoes),
        )
        .all()
    )

    for topico in todos_topicos:
        revisoes = topico.revisoes
        total = len(revisoes)
        ultima = max((r.criado_em for r in revisoes), default=None) if total > 0 else None
        status, _ = classificar_status_revisao(total, ultima, topico.criado_em, agora)
        if status is not None:
            total_pendentes_geral += 1

    # Agrupa tópicos por aluno para calcular progresso baseado em "em dia"
    topicos_por_aluno: dict[int, list] = {}
    for topico in todos_topicos:
        uid = topico.disciplina.user_id
        if uid not in topicos_por_aluno:
            topicos_por_aluno[uid] = []
        topicos_por_aluno[uid].append(topico)

    for aluno in alunos:
        aluno_topicos = topicos_por_aluno.get(aluno.id, [])
        total_topicos = len(aluno_topicos)

        topicos_em_dia = 0
        for topico in aluno_topicos:
            revisoes = topico.revisoes
            total = len(revisoes)
            ultima = max((r.criado_em for r in revisoes), default=None) if total > 0 else None
            status, _ = classificar_status_revisao(total, ultima, topico.criado_em, agora)
            if status is None:
                topicos_em_dia += 1

        total_revisoes = (
            db.query(sql_func.count(Revisao.id))
            .join(Topico, Topico.id == Revisao.topico_id)
            .join(Disciplina, Disciplina.id == Topico.disciplina_id)
            .filter(Disciplina.user_id == aluno.id, Revisao.criado_em >= inicio)
            .scalar()
        ) or 0

        ultima_revisao_dt = (
            db.query(sql_func.max(Revisao.criado_em))
            .join(Topico, Topico.id == Revisao.topico_id)
            .join(Disciplina, Disciplina.id == Topico.disciplina_id)
            .filter(Disciplina.user_id == aluno.id, Revisao.criado_em >= inicio)
            .scalar()
        )

        if ultima_revisao_dt:
            ultima_revisao_str = ultima_revisao_dt.strftime("%d/%m/%Y • %H:%M")
        else:
            ultima_revisao_str = "Nenhuma revisão"

        progresso = round((topicos_em_dia / total_topicos) * 100) if total_topicos > 0 else 0

        total_revisoes_geral += total_revisoes

        alunos_desempenho.append({
            "id": aluno.id,
            "nome": aluno.nome,
            "email": aluno.email,
            "iniciais": _iniciais(aluno.nome),
            "cor": _cor_avatar(aluno.id),
            "revisoes": total_revisoes,
            "ultimaRevisao": ultima_revisao_str,
            "progresso": progresso,
        })

    alunos_desempenho.sort(key=lambda a: a["revisoes"], reverse=True)

    total_alunos = len(alunos)
    media = round(total_revisoes_geral / total_alunos, 1) if total_alunos > 0 else 0

    return {
        "resumo": {
            "alunosAtivos": total_alunos,
            "revisoesRealizadas": total_revisoes_geral,
            "mediaRevisoesPorAluno": media,
            "revisoesPendentes": total_pendentes_geral,
        },
        "alunos": alunos_desempenho,
    }


def _classificar_urgencia(dias_atraso: int) -> str | None:
    """Classifica urgência baseado em dias de atraso desde a data prevista.

    < 7 dias de atraso  = None (não é considerado atrasado ainda)
    7-13 dias de atraso = Atrasado
    14+ dias de atraso  = Urgente
    """
    if dias_atraso < 7:
        return None
    if dias_atraso <= 13:
        return "Atrasado"
    return "Urgente"


def obter_pendencias_aluno(db: Session, aluno_id: int) -> dict | None:
    aluno = db.query(User).filter(User.id == aluno_id, User.role == RoleEnum.aluno).first()
    if not aluno:
        return None

    agora = datetime.now(MANAUS_TZ)
    hoje = agora.date()

    topicos = (
        db.query(Topico)
        .join(Disciplina, Disciplina.id == Topico.disciplina_id)
        .filter(Disciplina.user_id == aluno.id)
        .options(
            joinedload(Topico.disciplina),
            joinedload(Topico.revisoes),
        )
        .all()
    )

    topicos_pendentes = []
    contagem_por_disciplina: dict[str, int] = {}
    proxima_revisao_mais_cedo: tuple[date, str] | None = None

    for topico in topicos:
        revisoes = topico.revisoes
        total = len(revisoes)
        ultima = max((r.criado_em for r in revisoes), default=None) if total > 0 else None

        status, proxima = classificar_status_revisao(total, ultima, topico.criado_em, agora)

        # Rastreia a próxima revisão mais cedo entre todos os tópicos
        if proxima is not None:
            if proxima_revisao_mais_cedo is None or proxima < proxima_revisao_mais_cedo[0]:
                proxima_revisao_mais_cedo = (proxima, topico.titulo)

        if status is None:
            continue

        dias_atraso = max((hoje - proxima).days, 0) if proxima else 0

        if dias_atraso >= 14:
            urgencia = "Urgente"
        elif dias_atraso >= 7:
            urgencia = "Atrasado"
        else:
            urgencia = "Pendente"

        disc_nome = topico.disciplina.nome
        topicos_pendentes.append({
            "disciplina": disc_nome,
            "topico": topico.titulo,
            "dias": dias_atraso,
            "urgencia": urgencia,
        })

        contagem_por_disciplina[disc_nome] = contagem_por_disciplina.get(disc_nome, 0) + 1

    topicos_pendentes.sort(key=lambda t: t["dias"], reverse=True)

    # Última revisão global do aluno (independente de pendências)
    ultima_revisao_dt = (
        db.query(sql_func.max(Revisao.criado_em))
        .join(Topico, Topico.id == Revisao.topico_id)
        .join(Disciplina, Disciplina.id == Topico.disciplina_id)
        .filter(Disciplina.user_id == aluno.id)
        .scalar()
    )

    if ultima_revisao_dt:
        ultima_revisao_feita = _formatar_data_feed(ultima_revisao_dt, agora)
    else:
        ultima_revisao_feita = "Nenhuma revisão realizada"

    if contagem_por_disciplina:
        disc_mais = max(contagem_por_disciplina, key=contagem_por_disciplina.get)
        disciplina_mais_acumulada = disc_mais
    else:
        disciplina_mais_acumulada = "Nenhuma"

    # Próxima revisão recomendada (independente de pendências)
    if proxima_revisao_mais_cedo:
        data_proxima, topico_nome = proxima_revisao_mais_cedo
        dias_diff = (data_proxima - hoje).days
        if dias_diff < 0:
            proxima_recomendada = f"{topico_nome} - atrasado há {abs(dias_diff)} dias"
        elif dias_diff == 0:
            proxima_recomendada = f"{topico_nome} - revisão para hoje"
        elif dias_diff == 1:
            proxima_recomendada = f"{topico_nome} - amanhã"
        else:
            proxima_recomendada = f"{topico_nome} - em {dias_diff} dias ({data_proxima.strftime('%d/%m')})"
    else:
        proxima_recomendada = "Nenhuma revisão agendada"

    return {
        "nome": aluno.nome,
        "iniciais": _iniciais(aluno.nome),
        "cor": _cor_avatar(aluno.id),
        "topicosPendentes": topicos_pendentes,
        "ultimaRevisaoFeita": ultima_revisao_feita,
        "totalRevisoesPendentes": len(topicos_pendentes),
        "disciplinaMaisAcumulada": disciplina_mais_acumulada,
        "proximaRevisaoRecomendada": proxima_recomendada,
    }


def obter_revisoes_pendentes(db: Session) -> list[dict]:
    alunos = db.query(User).filter(User.role == RoleEnum.aluno).all()
    agora = datetime.now(MANAUS_TZ)
    hoje = agora.date()

    resultado = []

    for aluno in alunos:
        topicos = (
            db.query(Topico)
            .join(Disciplina, Disciplina.id == Topico.disciplina_id)
            .filter(Disciplina.user_id == aluno.id)
            .options(
                joinedload(Topico.disciplina),
                joinedload(Topico.revisoes),
            )
            .all()
        )

        tem_pendencia = False
        pior_urgencia = "Atrasado"
        maior_atraso = 0

        for topico in topicos:
            revisoes = topico.revisoes
            total = len(revisoes)
            ultima = max((r.criado_em for r in revisoes), default=None) if total > 0 else None
            status_rev, proxima = classificar_status_revisao(total, ultima, topico.criado_em, agora)
            if status_rev is not None:
                dias_atraso = max((hoje - proxima).days, 0) if proxima else 0
                urgencia = _classificar_urgencia(dias_atraso)
                if urgencia is None:
                    continue
                tem_pendencia = True
                if dias_atraso > maior_atraso:
                    maior_atraso = dias_atraso
                if urgencia == "Urgente":
                    pior_urgencia = "Urgente"
                elif urgencia == "Atrasado" and pior_urgencia != "Urgente":
                    pior_urgencia = "Atrasado"

        if not tem_pendencia:
            continue

        # Última revisão geral (sem filtro de período)
        ultima_revisao_dt = (
            db.query(sql_func.max(Revisao.criado_em))
            .join(Topico, Topico.id == Revisao.topico_id)
            .join(Disciplina, Disciplina.id == Topico.disciplina_id)
            .filter(Disciplina.user_id == aluno.id)
            .scalar()
        )

        if ultima_revisao_dt:
            ultima_revisao_str = _formatar_data_feed(ultima_revisao_dt, agora)
        else:
            ultima_revisao_str = "Nenhuma revisão"

        # Progresso geral (baseado em tópicos em dia)
        total_topicos = len(topicos)
        topicos_em_dia = 0
        disc_map: dict[str, dict] = {}

        for topico in topicos:
            revisoes_t = topico.revisoes
            total_rev = len(revisoes_t)
            ultima_rev = max((r.criado_em for r in revisoes_t), default=None) if total_rev > 0 else None
            status_t, _ = classificar_status_revisao(total_rev, ultima_rev, topico.criado_em, agora)

            disc_nome = topico.disciplina.nome
            if disc_nome not in disc_map:
                disc_map[disc_nome] = {"total": 0, "em_dia": 0}
            disc_map[disc_nome]["total"] += 1

            if status_t is None:
                topicos_em_dia += 1
                disc_map[disc_nome]["em_dia"] += 1

        progresso = round((topicos_em_dia / total_topicos) * 100) if total_topicos > 0 else 0

        disciplinas = [
            {
                "nome": nome,
                "percentual": round((v["em_dia"] / v["total"]) * 100) if v["total"] > 0 else 0,
            }
            for nome, v in disc_map.items()
        ]
        disciplinas.sort(key=lambda d: d["percentual"], reverse=True)

        # Últimas 5 revisões do aluno
        todas_revisoes = []
        for topico in topicos:
            for rev in topico.revisoes:
                todas_revisoes.append({
                    "topico": topico.titulo,
                    "reflexao": rev.reflexao or "Sem reflexão registrada.",
                    "data": _formatar_data_feed(rev.criado_em, agora),
                    "_criado_em": rev.criado_em,
                })
        todas_revisoes.sort(key=lambda r: r["_criado_em"], reverse=True)
        ultimas_revisoes = [
            {"topico": r["topico"], "reflexao": r["reflexao"], "data": r["data"]}
            for r in todas_revisoes[:5]
        ]

        resultado.append({
            "id": aluno.id,
            "nome": aluno.nome,
            "email": aluno.email,
            "iniciais": _iniciais(aluno.nome),
            "cor": _cor_avatar(aluno.id),
            "ultimaRevisao": ultima_revisao_str,
            "diasSemRevisar": maior_atraso,
            "situacao": pior_urgencia,
            "progressoGeral": progresso,
            "disciplinas": disciplinas,
            "ultimasRevisoes": ultimas_revisoes,
        })

    ordem_urgencia = {"Urgente": 0, "Atrasado": 1}
    resultado.sort(key=lambda a: (ordem_urgencia.get(a["situacao"], 3), -(a["diasSemRevisar"])))

    return resultado


def _calcular_sequencia_aluno(db: Session, user_id: int) -> int:
    """Calcula a sequência atual de revisões consecutivas feitas dentro do prazo."""
    topicos = (
        db.query(Topico)
        .join(Disciplina, Disciplina.id == Topico.disciplina_id)
        .filter(Disciplina.user_id == user_id)
        .options(joinedload(Topico.revisoes))
        .all()
    )

    revisoes_com_prazo: list[tuple[datetime, bool]] = []

    for topico in topicos:
        revisoes_ordenadas = sorted(topico.revisoes, key=lambda r: r.criado_em)
        for i, rev in enumerate(revisoes_ordenadas):
            if i == 0:
                data_esperada = calcular_proxima_revisao(0, None, topico.criado_em)
            else:
                data_esperada = calcular_proxima_revisao(
                    i, revisoes_ordenadas[i - 1].criado_em, topico.criado_em
                )

            if data_esperada is None:
                continue

            data_revisao = _to_manaus_date(rev.criado_em)
            no_prazo = data_revisao is not None and data_revisao <= data_esperada + timedelta(days=1)
            revisoes_com_prazo.append((rev.criado_em, no_prazo))

    revisoes_com_prazo.sort(key=lambda x: x[0], reverse=True)

    sequencia = 0
    for _, no_prazo in revisoes_com_prazo:
        if no_prazo:
            sequencia += 1
        else:
            break

    return sequencia


def _formatar_data_feed(dt: datetime, agora: datetime) -> str:
    data_revisao = _to_manaus_date(dt)
    hoje = agora.date()
    ontem = hoje - timedelta(days=1)
    hora = dt.strftime("%H:%M")

    if data_revisao == hoje:
        return f"Hoje • {hora}"
    if data_revisao == ontem:
        return f"Ontem • {hora}"
    return f"{data_revisao.strftime('%d/%m/%Y')} • {hora}"


def obter_atividade_recente(db: Session, periodo: str = "30dias") -> dict:
    agora = datetime.now(MANAUS_TZ)
    inicio = _calcular_inicio_periodo(periodo, agora)

    # --- Feed de atividades (últimas 20 revisões no período) ---
    revisoes_recentes = (
        db.query(Revisao)
        .join(Topico, Topico.id == Revisao.topico_id)
        .join(Disciplina, Disciplina.id == Topico.disciplina_id)
        .join(User, User.id == Disciplina.user_id)
        .filter(User.role == RoleEnum.aluno, Revisao.criado_em >= inicio)
        .options(
            joinedload(Revisao.topico).joinedload(Topico.disciplina).joinedload(Disciplina.usuario),
        )
        .order_by(Revisao.criado_em.desc())
        .limit(20)
        .all()
    )

    # Cache de sequência por aluno para evitar recalcular por item do feed
    cache_sequencia: dict[int, int] = {}

    feed = []
    for r in revisoes_recentes:
        aluno = r.topico.disciplina.usuario
        disc = r.topico.disciplina

        if aluno.id not in cache_sequencia:
            cache_sequencia[aluno.id] = _calcular_sequencia_aluno(db, aluno.id)

        feed.append({
            "nome": aluno.nome,
            "iniciais": _iniciais(aluno.nome),
            "cor": _cor_avatar(aluno.id),
            "topico": r.topico.titulo,
            "disciplina": disc.nome,
            "corDisciplina": disc.cor or "#6b7280",
            "data": _formatar_data_feed(r.criado_em, agora),
            "reflexao": r.reflexao or "Sem reflexão registrada.",
            "emSequencia": cache_sequencia[aluno.id],
        })

    # --- Tópicos com mais dificuldade (mais revisões no período) ---
    topicos_dificuldade_query = (
        db.query(
            Topico.titulo,
            Disciplina.nome.label("disciplina_nome"),
            sql_func.count(Revisao.id).label("total_revisoes"),
        )
        .join(Revisao, Revisao.topico_id == Topico.id)
        .join(Disciplina, Disciplina.id == Topico.disciplina_id)
        .join(User, User.id == Disciplina.user_id)
        .filter(User.role == RoleEnum.aluno, Revisao.criado_em >= inicio)
        .group_by(Topico.id, Topico.titulo, Disciplina.nome)
        .order_by(sql_func.count(Revisao.id).desc())
        .limit(5)
        .all()
    )

    max_revisoes = topicos_dificuldade_query[0].total_revisoes if topicos_dificuldade_query else 1
    topicos_dificuldade = [
        {
            "nome": t.titulo,
            "disciplina": t.disciplina_nome,
            "percentual": round((t.total_revisoes / max_revisoes) * 100),
        }
        for t in topicos_dificuldade_query
    ]

    # --- Alunos mais ativos (no período) ---
    alunos_ativos_query = (
        db.query(
            User.id,
            User.nome,
            sql_func.count(Revisao.id).label("total_revisoes"),
        )
        .join(Disciplina, Disciplina.user_id == User.id)
        .join(Topico, Topico.disciplina_id == Disciplina.id)
        .join(Revisao, Revisao.topico_id == Topico.id)
        .filter(User.role == RoleEnum.aluno, Revisao.criado_em >= inicio)
        .group_by(User.id, User.nome)
        .order_by(sql_func.count(Revisao.id).desc())
        .limit(5)
        .all()
    )

    alunos_ativos = [
        {
            "nome": a.nome,
            "iniciais": _iniciais(a.nome),
            "cor": _cor_avatar(a.id),
            "revisoes": a.total_revisoes,
            "posicao": idx + 1,
            "emSequencia": _calcular_sequencia_aluno(db, a.id),
        }
        for idx, a in enumerate(alunos_ativos_query)
    ]

    return {
        "feed": feed,
        "topicosDificuldade": topicos_dificuldade,
        "alunosMaisAtivos": alunos_ativos,
    }
