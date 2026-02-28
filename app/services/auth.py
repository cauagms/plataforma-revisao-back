from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.connection import get_db
from app.models.user import User, RoleEnum, BlacklistedToken
from app.schemas.user import UserCreate, TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, hash: str) -> bool:
    return pwd_context.verify(senha, hash)


def email_ja_cadastrado(db: Session, email: str) -> bool:
    return db.query(User).filter(User.email == email).first() is not None


def criar_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        if email is None:
            return None
        return TokenData(email=email, role=role)
    except JWTError:
        return None


def token_na_blacklist(db: Session, token: str) -> bool:
    return db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None


def invalidar_token(db: Session, token: str) -> None:
    db.add(BlacklistedToken(token=token))
    db.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    if token_na_blacklist(db, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token foi invalidado")

    dados_token = decodificar_token(token)
    if not dados_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    usuario = db.query(User).filter(User.email == dados_token.email).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")

    return usuario


def require_aluno(usuario: User = Depends(get_current_user)) -> User:
    if usuario.role != RoleEnum.aluno:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas alunos podem realizar esta ação",
        )
    return usuario


def cadastrar_usuario(db: Session, dados: UserCreate) -> User:
    usuario = User(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        role=RoleEnum.aluno,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> User | None:
    usuario = db.query(User).filter(User.email == email).first()
    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario