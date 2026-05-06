# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from auth import criar_access_token # O motor de criação do Token
from usuarios import autenticar_usuario # <--- ELA MORA AQUI!

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/token")
def login_para_acesso_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de Login. 
    O frontend envia 'username' e 'password' via form-data.
    """
    # 1. Tenta autenticar (usa a função que está no seu backend/auth.py)
    usuario = autenticar_usuario(db, form_data.username, form_data.password)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Prepara os dados para o crachá (Token)
    # Incluímos o 'sub' (nome de usuário) e o 'papel' (admin/operador)
    dados_token = {
        "sub": usuario.username,
        "papel": usuario.papel
    }

    # 3. Cria o token usando sua função criar_access_token
    token = criar_access_token(data=dados_token)

    # 4. Retorna para o Frontend (login.html)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 28800  # 8 horas em segundos
    }