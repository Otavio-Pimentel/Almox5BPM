# C:\5BPM\almoxarifado-pm\backend\usuarios.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Optional
from database import Base
from auth import gerar_hash_senha, verificar_senha

class Usuario(Base):
    __tablename__ = "usuarios"
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(50), unique=True, nullable=False, index=True)
    nome       = Column(String(150), nullable=False)
    senha_hash = Column(String(200), nullable=False)
    papel      = Column(String(20), nullable=False, default="operador")
    ativo      = Column(Boolean, default=True, nullable=False)
    criado_em  = Column(DateTime(timezone=True), server_default=func.now())

def buscar_usuario(db: Session, username: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.username == username, Usuario.ativo == True).first()

def autenticar_usuario(db: Session, username: str, senha: str) -> Optional[Usuario]:
    usuario = buscar_usuario(db, username)
    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario

def criar_usuario_inicial(db: Session) -> None:
    if db.query(Usuario).count() == 0:
        admin = Usuario(
            username="admin",
            nome="Administrador",
            senha_hash=gerar_hash_senha("admin123"),
            papel="admin",
            ativo=True
        )
        db.add(admin)
        db.commit()