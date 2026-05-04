# database.py - Configuração da conexão com o banco de dados SQLite
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Caminho do banco de dados - fica na pasta raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'almoxarifado.db')}"

# Criação do engine com suporte a threads (necessário para FastAPI)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Sessão do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos ORM
Base = declarative_base()

def get_db():
    """Gerador de sessão do banco de dados para injeção de dependência no FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
