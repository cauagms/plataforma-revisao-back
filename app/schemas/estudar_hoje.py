from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel


class StatusRevisao(str, Enum):
    atrasado = "atrasado"
    revisar_hoje = "revisar_hoje"
    primeira_revisao = "primeira_revisao"


class ResumoResponse(BaseModel):
    topicos_para_hoje: int
    pendentes: int
    atrasados: int
    revisar_hoje: int
    concluidos_hoje: int


class TopicoHojeResponse(BaseModel):
    disciplina_id: int
    topico_id: int
    topico: str
    disciplina: str
    cor_disciplina: str | None
    status: StatusRevisao
    ultima_revisao_em: datetime | None
    proxima_revisao_em: date | None
    total_revisoes: int


class EstudarHojeResponse(BaseModel):
    resumo: ResumoResponse
    topicos: list[TopicoHojeResponse]
