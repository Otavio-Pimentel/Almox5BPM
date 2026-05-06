# routers/itens.py - Rotas CRUD para Itens do Estoque
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from security import require_operador, require_admin
from usuarios import Usuario

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
def criar_item(
    dados:     ItemCreate,
    db:        Session = Depends(get_db),
    _operador: Usuario = Depends(require_operador),
):
    """
    Cria item ou incrementa quantidade existente.
    
    LÓGICA:
    ──────
    1. Se numero_serie → item SERIADO (arma, rádio)
       • Série deve ser ÚNICA (HTTP 409 se duplicado)
       • Sempre cria nova linha
    
    2. Se NÃO numero_serie → item GENÉRICO (munição, tonfa)
       • Busca por tipo_material + descricao
       • Se existe → incrementa quantidade
       • Se não existe → cria linha nova
    """
    
    # Validação básica
    if dados.quantidade_disponivel > dados.quantidade_total:
        raise HTTPException(
            status_code=422,
            detail="Quantidade disponível > quantidade total.",
        )
    
    # ─────────────────────────────────────────────────────
    # CASO 1: ITEM SERIADO (numero_serie presente)
    # ─────────────────────────────────────────────────────
    if dados.numero_serie:
        serie_norm = dados.numero_serie.upper().strip()
        
        # Verifica unicidade de série
        duplicado = db.query(Item).filter(
            Item.numero_serie == serie_norm
        ).first()
        
        if duplicado:
            raise HTTPException(
                status_code=409,
                detail=f"Série '{serie_norm}' já existe (ID {duplicado.id}).",
            )
        
        # Cria nova linha para seriado
        novo = Item(
            numero_serie=serie_norm,
            tipo_material=dados.tipo_material,
            descricao=dados.descricao,
            quantidade_total=dados.quantidade_total,
            quantidade_disponivel=dados.quantidade_disponivel,
            condicao=dados.condicao,
            localizacao=dados.localizacao or "",
            observacoes=dados.observacoes or "",
        )
        db.add(novo)
        db.commit()
        db.refresh(novo)
        return novo
    
    # ─────────────────────────────────────────────────────
    # CASO 2: ITEM NÃO-SERIADO (genérico)
    # ─────────────────────────────────────────────────────
    else:
        # Busca item idêntico
        existente = db.query(Item).filter(
            Item.numero_serie.is_(None),
            Item.tipo_material.ilike(dados.tipo_material),
            Item.descricao.ilike(dados.descricao),
        ).first()
        
        if existente:
            # ✔ Incrementa quantidade (sem criar linha nova)
            existente.quantidade_total += dados.quantidade_total
            existente.quantidade_disponivel += dados.quantidade_disponivel
            
            if dados.localizacao:
                existente.localizacao = dados.localizacao
            if dados.observacoes:
                existente.observacoes = dados.observacoes
            
            db.commit()
            db.refresh(existente)
            return existente
        
        else:
            # ✗ Item não existe → cria nova linha
            novo = Item(
                numero_serie=None,
                tipo_material=dados.tipo_material,
                descricao=dados.descricao,
                quantidade_total=dados.quantidade_total,
                quantidade_disponivel=dados.quantidade_disponivel,
                condicao=dados.condicao,
                localizacao=dados.localizacao or "",
                observacoes=dados.observacoes or "",
            )
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
