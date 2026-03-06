import re
from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum


class RoleEnum(str, Enum):
    aluno = "aluno"
    professor = "professor"


class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

    @field_validator("nome")
    @classmethod
    def nome_nao_vazio(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("Senha deve conter pelo menos uma letra minúscula")
        if not re.search(r"\d", v):
            raise ValueError("Senha deve conter pelo menos um número")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Senha deve conter pelo menos um caractere especial")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    senha: str


class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    role: RoleEnum

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None
