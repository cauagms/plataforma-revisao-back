from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import cadastrar_usuario, autenticar_usuario, criar_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(dados: UserCreate, db: Session = Depends(get_db)):
    from app.models.user import User
    usuario_existente = db.query(User).filter(User.email == dados.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    return cadastrar_usuario(db, dados)

@router.post("/login", response_model=Token)
def login(dados: UserLogin, db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, dados.email, dados.senha)
    if not usuario:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    token = criar_token({"sub": usuario.email, "role": usuario.role.value})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def me(db: Session = Depends(get_db), token: str = ""):
    from app.services.auth import decodificar_token
    dados_token = decodificar_token(token)
    if not dados_token:
        raise HTTPException(status_code=401, detail="Token inválido")
    from app.models.user import User
    usuario = db.query(User).filter(User.email == dados_token.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario