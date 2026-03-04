from datetime import datetime
from pydantic import BaseModel, field_validator


class TopicoCreate(BaseModel):
    titulo: str
    conteudo: str | None = None

    @field_validator("titulo")
    @classmethod
    def titulo_valido(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Título deve ter pelo menos 2 caracteres")
        return v


class TopicoUpdate(BaseModel):
    titulo: str | None = None
    conteudo: str | None = None

    @field_validator("titulo")
    @classmethod
    def titulo_valido(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Título deve ter pelo menos 2 caracteres")
        return v


class TopicoResponse(BaseModel):
    id: int
    titulo: str
    conteudo: str | None
    disciplina_id: int
    criado_em: datetime
    atualizado_em: datetime
    status: str = "Pendente"
    ultima_revisao_em: datetime | None = None
    total_revisoes: int = 0

    class Config:
        from_attributes = True
