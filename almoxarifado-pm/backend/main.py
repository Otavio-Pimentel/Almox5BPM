# main.py - Ponto de entrada do servidor FastAPI
# Sistema de Almoxarifado / Reserva de Armamentos - PMMG
import os
import sys

# Adiciona o diretório do backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import engine, Base, get_db
from models import Policial, Item, Cautela
from schemas import DashboardStats
from routers import policiais, itens, cautelas

# ─────────────────────────────────────────────────────────────
# CRIAÇÃO DAS TABELAS NO BANCO DE DADOS
# ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────────────────────
# INSTÂNCIA DO APP
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sistema de Almoxarifado PM",
    description="API para gerenciamento do Almoxarifado e Reserva de Armamentos",
    version="1.0.0"
)

# ─────────────────────────────────────────────────────────────
# CORS - Permite o frontend (HTML) consumir a API
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Em produção, restringir ao IP local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# REGISTRA OS ROTEADORES
# ─────────────────────────────────────────────────────────────
app.include_router(policiais.router)
app.include_router(itens.router)
app.include_router(cautelas.router)

# ─────────────────────────────────────────────────────────────
# SERVE OS ARQUIVOS ESTÁTICOS DO FRONTEND
# ─────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

    @app.get("/")
    def serve_dashboard():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/estoque")
    def serve_estoque():
        return FileResponse(os.path.join(FRONTEND_DIR, "estoque.html"))

    @app.get("/efetivo")
    def serve_efetivo():
        return FileResponse(os.path.join(FRONTEND_DIR, "efetivo.html"))

    @app.get("/painel-cautela")
    def serve_cautela():
        return FileResponse(os.path.join(FRONTEND_DIR, "cautelas.html"))


# ─────────────────────────────────────────────────────────────
# ROTA DO DASHBOARD - ESTATÍSTICAS
# ─────────────────────────────────────────────────────────────
@app.get("/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Retorna as estatísticas gerais para o painel principal."""
    agora = datetime.now(timezone.utc)

    total_policiais   = db.query(Policial).count()
    policiais_ativos  = db.query(Policial).filter(Policial.status == "Ativo").count()
    total_itens       = db.query(Item).count()
    itens_disponiveis = db.query(Item).filter(Item.quantidade_disponivel > 0).count()
    cautelas_ativas   = db.query(Cautela).filter(Cautela.status == "Ativa").count()
    itens_manutencao  = db.query(Item).filter(Item.condicao == "Precisa de Manutenção").count()
    itens_inservíveis = db.query(Item).filter(Item.condicao == "Inservível").count()

    # Cautelas em atraso: ativas com data prevista no passado
    from sqlalchemy import and_
    cautelas_atraso = db.query(Cautela).filter(
        and_(
            Cautela.status == "Ativa",
            Cautela.data_devolucao_prevista != None,
            Cautela.data_devolucao_prevista < agora
        )
    ).count()

    return DashboardStats(
        total_policiais=total_policiais,
        policiais_ativos=policiais_ativos,
        total_itens=total_itens,
        itens_disponiveis=itens_disponiveis,
        cautelas_ativas=cautelas_ativas,
        cautelas_em_atraso=cautelas_atraso,
        itens_em_manutencao=itens_manutencao,
        itens_inservíveis=itens_inservíveis,
    )


# ─────────────────────────────────────────────────────────────
# PONTO DE ENTRADA DIRETO (python main.py)
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("  🚔 SISTEMA DE ALMOXARIFADO - POLÍCIA MILITAR")
    print("=" * 55)
    print("  Servidor iniciando em: http://localhost:8000")
    print("  Documentação da API:   http://localhost:8000/docs")
    print("  Pressione CTRL+C para encerrar.")
    print("=" * 55)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
