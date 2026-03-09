from datetime import datetime
from pydantic import BaseModel


class ResumoHistorico(BaseModel):
    total_revisoes: int
    revisoes_semana: int
    disciplinas_revisadas: int
    ultima_revisao: datetime | None


class RevisaoHistorico(BaseModel):
    id: int
    topico_id: int
    topico: str
    disciplina_id: int
    disciplina: str
    cor_disciplina: str | None
    reflexao: str | None
    criado_em: datetime

    class Config:
        from_attributes = True


class HistoricoResponse(BaseModel):
    resumo: ResumoHistorico
    revisoes: list[RevisaoHistorico]
