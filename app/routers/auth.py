from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import (
    cadastrar_usuario,
    autenticar_usuario,
    criar_token,
    email_ja_cadastrado,
    get_current_user,
    invalidar_token,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, dados: UserCreate, db: Session = Depends(get_db)):
    if email_ja_cadastrado(db, dados.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado")
    return cadastrar_usuario(db, dados)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, dados: UserLogin, db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, dados.email, dados.senha)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos")
    token = criar_token({"sub": usuario.email, "role": usuario.role.value})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    invalidar_token(db, credentials.credentials)
    return {"detail": "Logout realizado com sucesso"}


@router.get("/me", response_model=UserResponse)
def me(usuario: User = Depends(get_current_user)):
    return usuario
