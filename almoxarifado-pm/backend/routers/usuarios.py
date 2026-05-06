# routers/usuarios.py - Gestão de Acessos e Auditoria Forense
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta

# Importações de Segurança e Banco
from database import get_db
from security import require_admin
from usuarios import Usuario
from models import Auditoria

router = APIRouter(prefix="/usuarios", tags=["Gestão e Auditoria"])

@router.get("/auditoria/")
def listar_auditoria(
    usuario_id: Optional[int] = Query(None, description="Filtrar por ID do Operador"),
    acao: Optional[str] = Query(None, description="Filtrar por tipo de ação"),
    dias: int = Query(7, ge=1, le=90, description="Dias de histórico"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin) # <-- TRAVA MÁXIMA: SÓ O COMANDO ACESSA
):
    """
    Lista o histórico de auditoria forense.
    NÍVEL DE ACESSO: Restrito a Administradores (Oficiais).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=dias)
    query = db.query(Auditoria).filter(Auditoria.data_hora >= cutoff)
    
    if usuario_id:
        query = query.filter(Auditoria.usuario_id == usuario_id)
    if acao:
        query = query.filter(Auditoria.acao == acao)
    
    return query.order_by(Auditoria.data_hora.desc()).all

