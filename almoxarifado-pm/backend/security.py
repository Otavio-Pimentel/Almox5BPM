# security.py - Dependências FastAPI para proteção de rotas
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from database import get_db
from auth import decodificar_token, TokenData
from usuarios import buscar_usuario, Usuario

# Esquema OAuth2 — o endpoint de token está em /auth/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ─────────────────────────────────────────────────────────────
# DEPENDÊNCIA BASE — extrai e valida o JWT do header Authorization
# ─────────────────────────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
) -> Usuario:
    """
    Extrai o JWT do header 'Authorization: Bearer <token>',
    valida assinatura e expiração, e retorna o usuário correspondente.
    Lança HTTP 401 em qualquer falha.
    """
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou sessão expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data: TokenData = decodificar_token(token)
    except JWTError:
        raise credenciais_invalidas

    usuario = buscar_usuario(db, token_data.username)
    if usuario is None:
        raise credenciais_invalidas
    return usuario


# ─────────────────────────────────────────────────────────────
# DEPENDÊNCIAS DE PAPEL (role-based access control)
# ─────────────────────────────────────────────────────────────
def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Permite acesso apenas a usuários com papel 'admin'."""
    if current_user.papel != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return current_user


def require_operador(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Permite acesso a 'admin' e 'operador'. Bloqueia papel 'leitura'."""
    if current_user.papel not in ("admin", "operador"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a operadores e administradores.",
        )
    return current_user
