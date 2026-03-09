from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserUpdate


def atualizar_perfil(db: Session, usuario: User, dados: UserUpdate) -> User:
    usuario.nome = dados.nome
    db.commit()
    db.refresh(usuario)
    return usuario
