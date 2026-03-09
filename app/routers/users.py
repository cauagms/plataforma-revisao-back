from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse
from app.services.auth import get_current_user
from app.services.user import atualizar_perfil

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserResponse)
def atualizar_meu_perfil(
    dados: UserUpdate,
    usuario: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return atualizar_perfil(db, usuario, dados)
