from datetime import datetime
from pydantic import BaseModel, field_validator


class DisciplinaCreate(BaseModel):
    nome: str
    descricao: str | None = None

    @field_validator("nome")
    @classmethod
    def nome_valido(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v


class DisciplinaUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None

    @field_validator("nome")
    @classmethod
    def nome_valido(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v


class DisciplinaResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None
    user_id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
