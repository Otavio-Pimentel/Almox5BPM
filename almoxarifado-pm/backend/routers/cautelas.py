# routers/cautelas.py - Rotas para o Sistema de Cautelas (Empréstimos e Devoluções)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import Cautela, Policial, Item
from schemas import CautelaCreate, CautelaDevolver, CautelaResponse

router = APIRouter(prefix="/cautelas", tags=["Cautelas"])


@router.get("/", response_model=List[CautelaResponse])
def listar_cautelas(
    status: Optional[str] = Query(None, description="Ativa | Devolvida"),
    policial_id: Optional[int] = Query(None),
    item_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Lista todas as cautelas com filtros e dados do policial e item incluídos."""
    query = db.query(Cautela).options(
        joinedload(Cautela.policial),
        joinedload(Cautela.item)
    )

    if status:
        query = query.filter(Cautela.status == status)
    if policial_id:
        query = query.filter(Cautela.policial_id == policial_id)
    if item_id:
        query = query.filter(Cautela.item_id == item_id)

    return query.order_by(Cautela.data_retirada.desc()).all()


@router.get("/em-atraso", response_model=List[CautelaResponse])
def cautelas_em_atraso(db: Session = Depends(get_db)):
    """Retorna cautelas ativas cuja data de devolução prevista já passou."""
    agora = datetime.now(timezone.utc)
    cautelas = db.query(Cautela).options(
        joinedload(Cautela.policial),
        joinedload(Cautela.item)
    ).filter(
        and_(
            Cautela.status == "Ativa",
            Cautela.data_devolucao_prevista != None,
            Cautela.data_devolucao_prevista < agora
        )
    ).all()
    return cautelas


@router.get("/{cautela_id}", response_model=CautelaResponse)
def obter_cautela(cautela_id: int, db: Session = Depends(get_db)):
    """Busca uma cautela pelo ID."""
    cautela = db.query(Cautela).options(
        joinedload(Cautela.policial),
        joinedload(Cautela.item)
    ).filter(Cautela.id == cautela_id).first()

    if not cautela:
        raise HTTPException(status_code=404, detail="Cautela não encontrada.")
    return cautela


@router.post("/", response_model=CautelaResponse, status_code=201)
def criar_cautela(dados: CautelaCreate, db: Session = Depends(get_db)):
    """
    Registra a retirada (saída) de um item pelo policial.
    Regras:
    - Policial deve existir e estar ativo.
    - Item deve existir e ter quantidade disponível.
    - Para itens seriados (armamento, colete), não permite acautelar o mesmo item duas vezes.
    """
    # Verifica se o policial existe e está ativo
    policial = db.query(Policial).filter(Policial.id == dados.policial_id).first()
    if not policial:
        raise HTTPException(status_code=404, detail="Policial não encontrado.")
    if policial.status not in ("Ativo", "Férias"):
        raise HTTPException(
            status_code=400,
            detail=f"Policial está com status '{policial.status}' e não pode retirar material."
        )

    # Verifica se o item existe
    item = db.query(Item).filter(Item.id == dados.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")

    # Verifica se o item está em condição de uso
    if item.condicao == "Inservível":
        raise HTTPException(status_code=400, detail="Item inservível não pode ser acautelado.")

    # Verifica disponibilidade de estoque
    if item.quantidade_disponivel < dados.quantidade:
        raise HTTPException(
            status_code=400,
            detail=f"Quantidade insuficiente. Disponível: {item.quantidade_disponivel}, Solicitado: {dados.quantidade}."
        )

    # Para itens seriados: verifica se já está na rua (cautela ativa)
    if item.numero_serie:
        cautela_existente = db.query(Cautela).filter(
            and_(Cautela.item_id == dados.item_id, Cautela.status == "Ativa")
        ).first()
        if cautela_existente:
            raise HTTPException(
                status_code=400,
                detail=f"Item '{item.descricao}' (Série: {item.numero_serie}) já está acautelado com {cautela_existente.policial.nome_guerra}."
            )

    # Cria a cautela
    nova_cautela = Cautela(
        policial_id=dados.policial_id,
        item_id=dados.item_id,
        quantidade=dados.quantidade,
        data_devolucao_prevista=dados.data_devolucao_prevista,
        responsavel_entrega=dados.responsavel_entrega,
        observacoes=dados.observacoes,
        status="Ativa"
    )
    db.add(nova_cautela)

    # Atualiza a quantidade disponível do item
    item.quantidade_disponivel -= dados.quantidade
    db.commit()
    db.refresh(nova_cautela)

    # Recarrega com os relacionamentos
    return db.query(Cautela).options(
        joinedload(Cautela.policial),
        joinedload(Cautela.item)
    ).filter(Cautela.id == nova_cautela.id).first()


@router.put("/{cautela_id}/devolver", response_model=CautelaResponse)
def devolver_item(cautela_id: int, dados: CautelaDevolver, db: Session = Depends(get_db)):
    """
    Registra a devolução de um item.
    Atualiza o status da cautela para 'Devolvida' e incrementa a quantidade disponível.
    """
    cautela = db.query(Cautela).options(
        joinedload(Cautela.item)
    ).filter(Cautela.id == cautela_id).first()

    if not cautela:
        raise HTTPException(status_code=404, detail="Cautela não encontrada.")
    if cautela.status == "Devolvida":
        raise HTTPException(status_code=400, detail="Esta cautela já foi devolvida.")

    # Atualiza a cautela
    cautela.status = "Devolvida"
    cautela.data_devolucao_real = dados.data_devolucao_real or datetime.now(timezone.utc)
    if dados.observacoes:
        cautela.observacoes = (cautela.observacoes or "") + f" | Devolução: {dados.observacoes}"

    # Devolve a quantidade ao estoque
    cautela.item.quantidade_disponivel += cautela.quantidade

    db.commit()
    db.refresh(cautela)

    return db.query(Cautela).options(
        joinedload(Cautela.policial),
        joinedload(Cautela.item)
    ).filter(Cautela.id == cautela_id).first()
