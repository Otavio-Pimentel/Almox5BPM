# routers/policiais.py - Rotas CRUD para Policiais
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import Policial
from schemas import PolicialCreate, PolicialUpdate, PolicialResponse

router = APIRouter(prefix="/policiais", tags=["Policiais"])


@router.get("/", response_model=List[PolicialResponse])
def listar_policiais(
    busca: Optional[str] = Query(None, description="Busca por matrícula ou nome de guerra"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    db: Session = Depends(get_db)
):
    """Lista todos os policiais com filtros opcionais."""
    query = db.query(Policial)

    if busca:
        query = query.filter(
            or_(
                Policial.matricula.ilike(f"%{busca}%"),
                Policial.nome_guerra.ilike(f"%{busca}%"),
                Policial.nome_completo.ilike(f"%{busca}%")
            )
        )
    if status:
        query = query.filter(Policial.status == status)

    return query.order_by(Policial.nome_guerra).all()


@router.get("/{policial_id}", response_model=PolicialResponse)
def obter_policial(policial_id: int, db: Session = Depends(get_db)):
    """Busca um policial pelo ID."""
    policial = db.query(Policial).filter(Policial.id == policial_id).first()
    if not policial:
        raise HTTPException(status_code=404, detail="Policial não encontrado.")
    return policial


@router.get("/matricula/{matricula}", response_model=PolicialResponse)
def buscar_por_matricula(matricula: str, db: Session = Depends(get_db)):
    """Busca um policial pela matrícula (RG PM). Usado no painel de cautela."""
    policial = db.query(Policial).filter(Policial.matricula == matricula).first()
    if not policial:
        raise HTTPException(status_code=404, detail=f"Policial com matrícula '{matricula}' não encontrado.")
    return policial


@router.post("/", response_model=PolicialResponse, status_code=201)
def criar_policial(dados: PolicialCreate, db: Session = Depends(get_db)):
    """Cadastra um novo policial no efetivo."""
    # Verifica se a matrícula já existe
    existente = db.query(Policial).filter(Policial.matricula == dados.matricula).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"Matrícula '{dados.matricula}' já cadastrada.")

    novo = Policial(**dados.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/{policial_id}", response_model=PolicialResponse)
def atualizar_policial(policial_id: int, dados: PolicialUpdate, db: Session = Depends(get_db)):
    """Atualiza dados de um policial."""
    policial = db.query(Policial).filter(Policial.id == policial_id).first()
    if not policial:
        raise HTTPException(status_code=404, detail="Policial não encontrado.")

    # Atualiza apenas os campos fornecidos
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(policial, campo, valor)

    db.commit()
    db.refresh(policial)
    return policial


@router.delete("/{policial_id}", status_code=204)
def deletar_policial(policial_id: int, db: Session = Depends(get_db)):
    """
    Remove um policial do sistema.
    ATENÇÃO: Não permite exclusão se houver cautelas ativas.
    """
    from models import Cautela
    policial = db.query(Policial).filter(Policial.id == policial_id).first()
    if not policial:
        raise HTTPException(status_code=404, detail="Policial não encontrado.")

    # Bloqueia exclusão se houver cautelas ativas
    cautelas_ativas = db.query(Cautela).filter(
        Cautela.policial_id == policial_id,
        Cautela.status == "Ativa"
    ).count()

    if cautelas_ativas > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir: policial possui {cautelas_ativas} cautela(s) ativa(s)."
        )

    db.delete(policial)
    db.commit()
