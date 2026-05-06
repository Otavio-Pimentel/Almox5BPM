# auth.py - Utilitários de autenticação usando Bcrypt Puro
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import bcrypt # <-- Usamos a biblioteca direto

from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "SUA_CHAVE_MESTRA_SUPER_SECRETA_5BPM")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 480 

class TokenData(BaseModel):
    username: Optional[str] = None
    papel:    Optional[str] = None

# ─────────────────────────────────────────────────────────────
# FUNÇÕES DE SENHA (SEM PASSLIB)
# ─────────────────────────────────────────────────────────────

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Verifica a senha plana contra o hash armazenado."""
    try:
        # O bcrypt precisa de bytes, por isso o .encode()
        return bcrypt.checkpw(
            senha_plana.encode('utf-8'), 
            senha_hash.encode('utf-8')
        )
    except Exception:
        return False

def gerar_hash_senha(senha: str) -> str:
    """Gera um hash seguro usando bcrypt."""
    # Gera o salt e o hash em um passo só
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(senha.encode('utf-8'), salt)
    return hash_bytes.decode('utf-8')

# ─────────────────────────────────────────────────────────────
# JWT (Lógica de Token)
# ─────────────────────────────────────────────────────────────

def criar_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        papel:    Optional[str] = payload.get("papel")
        if username is None:
            raise JWTError("Sub ausente")
        return TokenData(username=username, papel=papel)
    except JWTError:
        raise