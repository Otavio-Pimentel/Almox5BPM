# routers/cautelas.py - Rotas para o Sistema de Cautelas (Empréstimos e Devoluções)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import Request
from sqlalchemy import update
from auditoria import registrar_auditoria, extrair_dados_do_objeto
from security import require_operador
from usuarios import Usuario
from typing import List, Optional
from datetime import datetime, timezone


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
def criar_cautela(
    dados: CautelaCreate, 
    request: Request, 
    db: Session = Depends(get_db), 
    _operador: Usuario = Depends(require_operador) # <-- TRAVA DE ACESSO
):
    """Registra a retirada (saída) de um item pelo policial com auditoria forense."""
    policial = db.query(Policial).filter(Policial.id == dados.policial_id).first()
    if not policial or policial.status not in ("Ativo", "Férias"):
        raise HTTPException(status_code=400, detail="Policial inválido ou inativo.")

    item = db.query(Item).filter(Item.id == dados.item_id).first()
    if not item or item.condicao == "Inservível" or item.quantidade_disponivel < dados.quantidade:
        raise HTTPException(status_code=400, detail="Item indisponível ou inservível.")

    if item.numero_serie:
        cautela_existente = db.query(Cautela).filter(
            and_(Cautela.item_id == dados.item_id, Cautela.status == "Ativa")
        ).first()
        if cautela_existente:
            raise HTTPException(status_code=400, detail=f"Item (Série: {item.numero_serie}) já está acautelado.")

    nova_cautela = Cautela(**dados.dict(), status="Ativa")
    db.add(nova_cautela)
    item.quantidade_disponivel -= dados.quantidade
    db.commit()
    db.refresh(nova_cautela)
    
    # 📝 REGISTRO DE AUDITORIA FORENSE INEGOCIÁVEL
    registrar_auditoria(
        db=db, usuario_id=_operador.id, acao="criar_cautela", tabela_afetada="cautelas", registro_id=nova_cautela.id,
        dados_novos=extrair_dados_do_objeto(nova_cautela, ["policial_id", "item_id", "quantidade", "status"]),
        ip_address=request.client.host if request.client else "desconhecido",
        user_agent=request.headers.get("user-agent", "desconhecido")
    )
    return db.query(Cautela).options(joinedload(Cautela.policial), joinedload(Cautela.item)).filter(Cautela.id == nova_cautela.id).first()


@router.put("/{cautela_id}/devolver", response_model=CautelaResponse)
def devolver_item(
    cautela_id: int, 
    dados: CautelaDevolver, 
    request: Request, 
    db: Session = Depends(get_db), 
    _operador: Usuario = Depends(require_operador) # <-- TRAVA DE ACESSO
):
    """Registra a devolução de um item utilizando atualização atômica e whitelist de status."""
    cautela = db.query(Cautela).filter(Cautela.id == cautela_id).first()
    if not cautela: 
        raise HTTPException(status_code=404, detail="Cautela não encontrada.")
    
    # 🛡️ WHITELIST TÁTICA: Bloqueia devolução de itens cancelados ou extraviados
    if cautela.status != "Ativa":
        raise HTTPException(status_code=409, detail=f"Cautela com status '{cautela.status}' não pode ser devolvida.")
    
    # Captura foto do estado atual para a auditoria
    dados_antes = extrair_dados_do_objeto(cautela, ["status", "data_devolucao_real", "observacoes"])
    
    agora = datetime.now(timezone.utc)
    data_dev = dados.data_devolucao_real or agora
    
    # 🛡️ ATUALIZAÇÃO ATÔMICA DA CAUTELA (Previne falhas de concorrência)
    db.execute(
        update(Cautela).where(and_(Cautela.id == cautela_id, Cautela.status == "Ativa"))
        .values(status="Devolvida", data_devolucao_real=data_dev, observacoes=(
            ((cautela.observacoes or "") + f" | Devolução: {dados.observacoes}").strip(" |") if dados.observacoes else cautela.observacoes
        ))
    )
    
    # 🛡️ ATUALIZAÇÃO ATÔMICA DO ESTOQUE
    db.execute(
        update(Item).where(Item.id == cautela.item_id)
        .values(quantidade_disponivel=min(Item.quantidade_disponivel + cautela.quantidade, Item.quantidade_total))
    )
    db.commit()
    
    cautela_atualizada = db.query(Cautela).filter(Cautela.id == cautela_id).first()
    dados_depois = extrair_dados_do_objeto(cautela_atualizada, ["status", "data_devolucao_real", "observacoes"])
    
    # 📝 REGISTRO DE AUDITORIA FORENSE INEGOCIÁVEL
    registrar_auditoria(
        db=db, usuario_id=_operador.id, acao="devolver_item", tabela_afetada="cautelas", registro_id=cautela_id,
        dados_anteriores=dados_antes, dados_novos=dados_depois,
        ip_address=request.client.host if request.client else "desconhecido", 
        user_agent=request.headers.get("user-agent", "desconhecido")
    )
    
    return db.query(Cautela).options(joinedload(Cautela.policial), joinedload(Cautela.item)).filter(Cautela.id == cautela_id).first()