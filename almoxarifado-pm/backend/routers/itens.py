# routers/itens.py - Rotas CRUD para Itens do Estoque
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import Item
from schemas import ItemCreate, ItemUpdate, ItemResponse

router = APIRouter(prefix="/itens", tags=["Itens"])


@router.get("/", response_model=List[ItemResponse])
def listar_itens(
    busca: Optional[str] = Query(None, description="Busca por descrição ou número de série"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de material"),
    condicao: Optional[str] = Query(None, description="Filtrar por condição"),
    apenas_disponiveis: Optional[bool] = Query(False, description="Mostrar apenas itens disponíveis"),
    db: Session = Depends(get_db)
):
    """Lista todos os itens do estoque com filtros."""
    query = db.query(Item)

    if busca:
        query = query.filter(
            or_(
                Item.descricao.ilike(f"%{busca}%"),
                Item.numero_serie.ilike(f"%{busca}%")
            )
        )
    if tipo:
        query = query.filter(Item.tipo_material == tipo)
    if condicao:
        query = query.filter(Item.condicao == condicao)
    if apenas_disponiveis:
        query = query.filter(Item.quantidade_disponivel > 0)

    return query.order_by(Item.tipo_material, Item.descricao).all()


@router.get("/{item_id}", response_model=ItemResponse)
def obter_item(item_id: int, db: Session = Depends(get_db)):
    """Busca um item pelo ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return item


@router.get("/serie/{numero_serie}", response_model=ItemResponse)
def buscar_por_serie(numero_serie: str, db: Session = Depends(get_db)):
    """Busca um item pelo número de série. Usado com leitor de código de barras."""
    item = db.query(Item).filter(Item.numero_serie == numero_serie).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item com nº série '{numero_serie}' não encontrado.")
    return item


@router.post("/", response_model=ItemResponse, status_code=201)
def criar_item(dados: ItemCreate, db: Session = Depends(get_db)):
    """Cadastra um novo item no estoque."""
    # Verifica duplicidade de número de série (apenas se fornecido)
    if dados.numero_serie:
        existente = db.query(Item).filter(Item.numero_serie == dados.numero_serie).first()
        if existente:
            raise HTTPException(
                status_code=400,
                detail=f"Número de série '{dados.numero_serie}' já cadastrado."
            )

    # Garante que quantidade disponível não excede o total
    if dados.quantidade_disponivel > dados.quantidade_total:
        raise HTTPException(
            status_code=400,
            detail="Quantidade disponível não pode ser maior que a quantidade total."
        )

    novo = Item(**dados.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/{item_id}", response_model=ItemResponse)
def atualizar_item(item_id: int, dados: ItemUpdate, db: Session = Depends(get_db)):
    """Atualiza dados de um item do estoque."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")

    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(item, campo, valor)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def deletar_item(item_id: int, db: Session = Depends(get_db)):
    """
    Remove um item do sistema.
    ATENÇÃO: Não permite exclusão se houver cautelas ativas para o item.
    """
    from models import Cautela
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")

    cautelas_ativas = db.query(Cautela).filter(
        Cautela.item_id == item_id,
        Cautela.status == "Ativa"
    ).count()

    if cautelas_ativas > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir: item possui {cautelas_ativas} cautela(s) ativa(s)."
        )

    db.delete(item)
    db.commit()
