# apps/estoque/models.py
#
# Model de domínio: Item (estoque)
#
# Fonte de referência:
#   SQLAlchemy → class Item (__tablename__ = "itens")
#   Pydantic   → ItemBase / ItemResponse
#
# Preservação de contrato:
#   Todos os nomes de campo, tipos e regras de nullable são idênticos
#   ao modelo SQLAlchemy de origem.
#
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords


class Item(models.Model):
    """
    Representa um item do estoque de armamentos/materiais.

    Dois tipos operacionais (lógica de negócio preservada):
        Seriado (numero_serie preenchido):
            → Unicidade absoluta (arma, rádio HT, colete)
            → Uma linha por item físico
            → Não pode estar em duas cautelas ativas simultâneas

        Genérico / Lote (numero_serie = null):
            → Controlado por quantidade
            → Pode haver múltiplas cautelas ativas (até esgotar disponibilidade)
            → Ao cadastrar o mesmo tipo+descrição, quantidade é incrementada
    """

    # ── Enums de domínio ─────────────────────────────────────
    class TipoMaterial(models.TextChoices):
        ARMAMENTO  = 'Armamento',      'Armamento'
        MUNICAO    = 'Munição',         'Munição'
        COLETE     = 'Colete Balístico', 'Colete Balístico'
        RADIO      = 'Rádio HT',        'Rádio HT'
        VIATURA    = 'Viatura',         'Viatura'
        FARDAMENTO = 'Fardamento',      'Fardamento'
        DIVERSOS   = 'Diversos',        'Diversos'

    class Condicao(models.TextChoices):
        NOVO        = 'Novo',                  'Novo'
        BOM         = 'Bom',                   'Bom'
        MANUTENCAO  = 'Precisa de Manutenção', 'Precisa de Manutenção'
        INSERVIVEL  = 'Inservível',             'Inservível'

    # ── Campos ───────────────────────────────────────────────
    numero_serie = models.CharField(
        max_length=100,
        unique=True,      # UNIQUE — garante unicidade de item seriado
        null=True,        # null=True → item genérico/lote
        blank=True,
        db_index=True,
        verbose_name='Número de série',
        help_text='Preencha apenas para itens individualizados (armas, rádios). '
                  'Deixe vazio para itens de lote (munição, fardamento).',
    )
    tipo_material = models.CharField(
        max_length=30,
        choices=TipoMaterial.choices,
        verbose_name='Tipo de material',
    )
    descricao = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        verbose_name='Descrição',
    )
    quantidade_total = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade total',
        help_text='Total físico existente no almoxarifado.',
    )
    quantidade_disponivel = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade disponível',
        help_text='Total disponível para acautelar (total − acautelados).',
    )
    condicao = models.CharField(
        max_length=30,
        choices=Condicao.choices,
        default=Condicao.BOM,
        verbose_name='Condição',
    )
    localizacao = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Localização',
        help_text='Ex: Prateleira A3, Armário 2.',
    )
    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações',
    )

    # ── Timestamps ───────────────────────────────────────────
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em',
    )

    # ── Auditoria automática de campo ─────────────────────────
    history = HistoricalRecords()

    class Meta:
        verbose_name        = 'Item'
        verbose_name_plural = 'Itens'
        ordering            = ['tipo_material', 'descricao']
        # db_table = 'itens'  # Descomente na etapa de migração de dados
        constraints = [
            # Garante que quantidade_disponivel <= quantidade_total no banco
            models.CheckConstraint(
                condition=models.Q(quantidade_disponivel__lte=models.F('quantidade_total')),
                name='item_disponivel_lte_total',
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade_total__gte=0),
                name='item_total_gte_zero',
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade_disponivel__gte=0),
                name='item_disponivel_gte_zero',
            ),
        ]

    def __str__(self) -> str:
        serie = f' [{self.numero_serie}]' if self.numero_serie else ''
        return f'{self.tipo_material} — {self.descricao}{serie}'

    @property
    def is_seriado(self) -> bool:
        return bool(self.numero_serie)

    @property
    def is_disponivel(self) -> bool:
        return self.quantidade_disponivel > 0 and self.condicao != self.Condicao.INSERVIVEL
