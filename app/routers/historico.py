from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.historico import HistoricoResponse
from app.services.auth import get_current_user
from app.services import historico as service

router = APIRouter(
    prefix="/historico",
    tags=["Histórico"],
)


@router.get("", response_model=HistoricoResponse)
def historico(
    disciplina_id: int | None = Query(None),
    periodo: str | None = Query(None),
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return service.obter_historico(
        db,
        usuario,
        disciplina_id=disciplina_id,
        periodo=periodo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
