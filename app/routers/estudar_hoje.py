from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.estudar_hoje import EstudarHojeResponse
from app.services.auth import get_current_user
from app.services import estudar_hoje as service

router = APIRouter(
    prefix="/estudar-hoje",
    tags=["Estudar Hoje"],
)


@router.get("", response_model=EstudarHojeResponse)
def estudar_hoje(
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return service.obter_estudar_hoje(db, usuario)
