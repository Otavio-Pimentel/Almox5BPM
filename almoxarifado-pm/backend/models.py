# models.py - Modelos do banco de dados (tabelas SQLite via SQLAlchemy)
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────
class PostoGraduacao(str, enum.Enum):
    SD   = "Sd"
    CB   = "Cb"
    SGT  = "Sgt"
    STTEN = "Sub Ten"
    TEN  = "Ten"
    CAP  = "Cap"
    MAJ  = "Maj"
    TC   = "TC"
    CEL  = "Cel"

class StatusPolicial(str, enum.Enum):
    ATIVO  = "Ativo"
    FERIAS = "Férias"
    LICENCA = "Licença"
    INATIVO = "Inativo"

class TipoMaterial(str, enum.Enum):
    ARMAMENTO       = "Armamento"
    MUNICAO         = "Munição"
    COLETE          = "Colete Balístico"
    RADIO           = "Rádio HT"
    VIATURA         = "Viatura"
    FARDAMENTO      = "Fardamento"
    DIVERSOS        = "Diversos"

class CondicaoItem(str, enum.Enum):
    NOVO            = "Novo"
    BOM             = "Bom"
    MANUTENCAO      = "Precisa de Manutenção"
    INSERVIVEL      = "Inservível"


# ─────────────────────────────────────────────────────────────
# TABELA: POLICIAIS
# ─────────────────────────────────────────────────────────────
class Policial(Base):
    __tablename__ = "policiais"

    id                 = Column(Integer, primary_key=True, index=True)
    matricula          = Column(String(20), unique=True, nullable=False, index=True)
    nome_guerra        = Column(String(100), nullable=False)
    nome_completo      = Column(String(200), nullable=True)
    posto_graduacao    = Column(String(20), nullable=False)
    companhia_pelotao  = Column(String(50), nullable=True)
    status             = Column(String(20), default="Ativo", nullable=False)
    criado_em          = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamento: um policial pode ter várias cautelas
    cautelas = relationship("Cautela", back_populates="policial")


# ─────────────────────────────────────────────────────────────
# TABELA: ITENS (Estoque)
# ─────────────────────────────────────────────────────────────
class Item(Base):
    __tablename__ = "itens"

    id                   = Column(Integer, primary_key=True, index=True)
    numero_serie         = Column(String(100), unique=True, nullable=True, index=True)
    tipo_material        = Column(String(30), nullable=False)
    descricao            = Column(String(200), nullable=False)
    quantidade_total     = Column(Integer, default=1, nullable=False)
    quantidade_disponivel = Column(Integer, default=1, nullable=False)
    condicao             = Column(String(30), default="Bom", nullable=False)
    localizacao          = Column(String(100), nullable=True)  # Ex: "Prateleira A3"
    observacoes          = Column(Text, nullable=True)
    criado_em            = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em        = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamento: um item pode estar em várias cautelas (histórico)
    cautelas = relationship("Cautela", back_populates="item")


# ─────────────────────────────────────────────────────────────
# TABELA: CAUTELAS
# ─────────────────────────────────────────────────────────────
class Cautela(Base):
    __tablename__ = "cautelas"

    id                      = Column(Integer, primary_key=True, index=True)
    policial_id             = Column(Integer, ForeignKey("policiais.id"), nullable=False)
    item_id                 = Column(Integer, ForeignKey("itens.id"), nullable=False)
    quantidade              = Column(Integer, default=1, nullable=False)
    data_retirada           = Column(DateTime(timezone=True), server_default=func.now())
    data_devolucao_prevista = Column(DateTime(timezone=True), nullable=True)
    data_devolucao_real     = Column(DateTime(timezone=True), nullable=True)
    responsavel_entrega     = Column(String(100), nullable=False)
    status                  = Column(String(20), default="Ativa", nullable=False)  # Ativa | Devolvida
    observacoes             = Column(Text, nullable=True)
    criado_em               = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    policial = relationship("Policial", back_populates="cautelas")
    item     = relationship("Item", back_populates="cautelas")
