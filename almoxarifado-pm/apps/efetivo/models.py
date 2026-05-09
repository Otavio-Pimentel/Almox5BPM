# apps/efetivo/models.py
#
# Model de domínio: Policial
#
# Fonte de referência:
#   SQLAlchemy → class Policial (__tablename__ = "policiais")
#   Pydantic   → PolicialBase / PolicialResponse
#
# Preservação de contrato:
#   Todos os nomes de campo, tipos e regras de nullable são idênticos
#   ao modelo SQLAlchemy de origem para garantir compatibilidade de payload.
#
from django.core.validators import MinLengthValidator
from django.db import models
from simple_history.models import HistoricalRecords


class Policial(models.Model):
    """
    Representa um policial do efetivo do batalhão.

    Regras de negócio preservadas:
        - matricula é UNIQUE e indexada (usada como chave de busca no painel de cautela)
        - Apenas policiais com status Ativo ou Férias podem retirar material
        - Soft delete: status muda para Inativo (nunca DELETE real)
    """

    # ── Enums de domínio ─────────────────────────────────────
    class PostoGraduacao(models.TextChoices):
        SD     = 'Sd',      'Soldado'
        CB     = 'Cb',      'Cabo'
        SGT    = 'Sgt',     'Sargento'
        SUB_TEN = 'Sub Ten', 'Subtenente'
        TEN    = 'Ten',     'Tenente'
        CAP    = 'Cap',     'Capitão'
        MAJ    = 'Maj',     'Major'
        TC     = 'TC',      'Tenente-Coronel'
        CEL    = 'Cel',     'Coronel'

    class Status(models.TextChoices):
        ATIVO   = 'Ativo',   'Ativo'
        FERIAS  = 'Férias',  'Férias'
        LICENCA = 'Licença', 'Licença'
        INATIVO = 'Inativo', 'Inativo'

    # ── Campos ───────────────────────────────────────────────
    matricula = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        validators=[MinLengthValidator(1)],
        verbose_name='Matrícula / RG PM',
    )
    nome_guerra = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        verbose_name='Nome de guerra',
    )
    nome_completo = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='Nome completo',
    )
    posto_graduacao = models.CharField(
        max_length=20,
        choices=PostoGraduacao.choices,
        verbose_name='Posto / Graduação',
    )
    companhia_pelotao = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Companhia / Pelotão',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
        verbose_name='Status',
    )

    # ── Timestamps ───────────────────────────────────────────
    # auto_now_add equivale a server_default=func.now() + NOT NULL
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )
    # auto_now equivale a onupdate=func.now()
    # Diferença: Django também preenche na criação (comportamento mais seguro)
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em',
    )

    # ── Auditoria automática de campo ─────────────────────────
    history = HistoricalRecords()

    class Meta:
        verbose_name        = 'Policial'
        verbose_name_plural = 'Policiais'
        ordering            = ['nome_guerra']
        # db_table = 'policiais'  # Descomente na etapa de migração de dados

    def __str__(self) -> str:
        return f'{self.posto_graduacao} {self.nome_guerra} ({self.matricula})'

    @property
    def pode_retirar_material(self) -> bool:
        """Regra de negócio: apenas Ativo e Férias podem acautelar."""
        return self.status in (self.Status.ATIVO, self.Status.FERIAS)
