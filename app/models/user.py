from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


class RoleEnum(str, enum.Enum):
    aluno = "aluno"
    professor = "professor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.aluno, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    disciplinas = relationship("Disciplina", back_populates="usuario", cascade="all, delete-orphan")


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    invalidado_em = Column(DateTime(timezone=True), server_default=func.now())