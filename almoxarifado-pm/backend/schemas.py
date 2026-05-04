# schemas.py - Schemas Pydantic para validação de dados da API
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# SCHEMAS DE POLICIAL
# ─────────────────────────────────────────────────────────────
class PolicialBase(BaseModel):
    matricula:         str = Field(..., min_length=1, max_length=20, description="Matrícula / RG PM")
    nome_guerra:       str = Field(..., min_length=2, max_length=100)
    nome_completo:     Optional[str] = None
    posto_graduacao:   str
    companhia_pelotao: Optional[str] = None
    status:            str = "Ativo"

class PolicialCreate(PolicialBase):
    pass

class PolicialUpdate(BaseModel):
    nome_guerra:       Optional[str] = None
    nome_completo:     Optional[str] = None
    posto_graduacao:   Optional[str] = None
    companhia_pelotao: Optional[str] = None
    status:            Optional[str] = None

class PolicialResponse(PolicialBase):
    id:         int
    criado_em:  Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# SCHEMAS DE ITEM
# ─────────────────────────────────────────────────────────────
class ItemBase(BaseModel):
    numero_serie:          Optional[str] = None
    tipo_material:         str
    descricao:             str = Field(..., min_length=2, max_length=200)
    quantidade_total:      int = Field(default=1, ge=0)
    quantidade_disponivel: int = Field(default=1, ge=0)
    condicao:              str = "Bom"
    localizacao:           Optional[str] = None
    observacoes:           Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    numero_serie:          Optional[str] = None
    tipo_material:         Optional[str] = None
    descricao:             Optional[str] = None
    quantidade_total:      Optional[int] = None
    quantidade_disponivel: Optional[int] = None
    condicao:              Optional[str] = None
    localizacao:           Optional[str] = None
    observacoes:           Optional[str] = None

class ItemResponse(ItemBase):
    id:           int
    criado_em:    Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# SCHEMAS DE CAUTELA
# ─────────────────────────────────────────────────────────────
class CautelaBase(BaseModel):
    policial_id:             int
    item_id:                 int
    quantidade:              int = Field(default=1, ge=1)
    data_devolucao_prevista: Optional[datetime] = None
    responsavel_entrega:     str = Field(..., min_length=2, max_length=100)
    observacoes:             Optional[str] = None

class CautelaCreate(CautelaBase):
    pass

class CautelaDevolver(BaseModel):
    data_devolucao_real: Optional[datetime] = None
    observacoes:         Optional[str] = None

class CautelaResponse(CautelaBase):
    id:                  int
    status:              str
    data_retirada:       Optional[datetime] = None
    data_devolucao_real: Optional[datetime] = None
    criado_em:           Optional[datetime] = None
    policial:            Optional[PolicialResponse] = None
    item:                Optional[ItemResponse]     = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# SCHEMA DO DASHBOARD
# ─────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_policiais:        int
    policiais_ativos:       int
    total_itens:            int
    itens_disponiveis:      int
    cautelas_ativas:        int
    cautelas_em_atraso:     int
    itens_em_manutencao:    int
    itens_inservíveis:      int
