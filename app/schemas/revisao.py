from datetime import datetime
from pydantic import BaseModel


class RevisaoCreate(BaseModel):
    reflexao: str | None = None


class RevisaoResponse(BaseModel):
    id: int
    topico_id: int
    reflexao: str | None
    criado_em: datetime

    class Config:
        from_attributes = True
