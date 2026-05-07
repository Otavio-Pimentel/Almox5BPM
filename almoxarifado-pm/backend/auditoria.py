# auditoria.py
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import Auditoria
from typing import Optional, Any, Dict

def registrar_auditoria(
    db: Session, usuario_id: int, acao: str, tabela_afetada: str, registro_id: int,
    dados_anteriores: Optional[Dict[str, Any]] = None,
    dados_novos: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None, user_agent: Optional[str] = None,
) -> Auditoria:
    
    ACOES_VALIDAS = {"criar_cautela", "devolver_item", "criar_item", "alterar_item", "deletar_item", "criar_policial", "alterar_policial", "deletar_policial", "alterar_senha", "criar_usuario", "deletar_usuario"}
    
    if acao not in ACOES_VALIDAS: raise ValueError(f"Ação inválida: {acao}.")
    
    dados_ant_str = json.dumps(dados_anteriores or {}, ensure_ascii=False, default=str)
    dados_nov_str = json.dumps(dados_novos or {}, ensure_ascii=False, default=str)
    
    audit = Auditoria(
        usuario_id=usuario_id, acao=acao, tabela_afetada=tabela_afetada, registro_id=registro_id,
        dados_anteriores=dados_ant_str, dados_novos=dados_nov_str, ip_address=ip_address, user_agent=user_agent
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit

def extrair_dados_do_objeto(obj: Any, campos: list[str]) -> Dict[str, Any]:
    resultado = {}
    for campo in campos:
        if hasattr(obj, campo):
            valor = getattr(obj, campo)
            if hasattr(valor, "isoformat"): valor = valor.isoformat()
            resultado[campo] = valor
    return resultado