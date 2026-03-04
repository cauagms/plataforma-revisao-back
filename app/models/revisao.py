from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Revisao(Base):
    __tablename__ = "revisoes"

    id = Column(Integer, primary_key=True, index=True)
    topico_id = Column(Integer, ForeignKey("topicos.id", ondelete="CASCADE"), nullable=False)
    reflexao = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    topico = relationship("Topico", back_populates="revisoes")
