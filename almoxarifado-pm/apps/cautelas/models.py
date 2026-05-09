# apps/cautelas/models.py
#
# Model de domínio: Cautela (controle de empréstimos e devoluções)
#
# Fonte de referência:
#   SQLAlchemy → class Cautela (__tablename__ = "cautelas")
#   Pydantic   → CautelaBase / CautelaResponse
#
# Preservação de contrato:
#   ForeignKeys para Policial e Item com on_delete=PROTECT
#   (nunca deletar policial ou item com cautelas existentes).
#
from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class Cautela(models.Model):
    """
    Representa uma operação de empréstimo de material.

    Máquina de estados (WHITELIST explícita):
        Ativa     → estado inicial após criação
        Devolvida → único estado de destino válido via PUT /devolver

        REGRA CRÍTICA: A devolução só é permitida se status == 'Ativa'.
        Qualquer outro status bloqueia a operação (HTTP 409).
        Isso previne corrupção de estoque caso novos status sejam
        adicionados no futuro (Cancelada, Extraviada, Em Manutenção).

    Integridade de estoque:
        - Criação:  quantidade_disponivel -= quantidade (UPDATE atômico)
        - Devolução: quantidade_disponivel += quantidade (capped em total)
    """

    class Status(models.TextChoices):
        ATIVA     = 'Ativa',     'Ativa'
        DEVOLVIDA = 'Devolvida', 'Devolvida'
        # Novos status DEVEM ser adicionados aqui antes de usados na view.
        # A view valida com whitelist: if cautela.status != 'Ativa' → 409.

    # ── Relacionamentos (FK) ─────────────────────────────────
    policial = models.ForeignKey(
        'efetivo.Policial',
        on_delete=models.PROTECT,     # Não permite deletar policial com cautelas
        related_name='cautelas',
        verbose_name='Policial',
    )
    item = models.ForeignKey(
        'estoque.Item',
        on_delete=models.PROTECT,     # Não permite deletar item com cautelas
        related_name='cautelas',
        verbose_name='Item',
    )

    # ── Campos operacionais ──────────────────────────────────
    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantidade',
        help_text='Quantidade retirada. Mínimo 1.',
    )
    data_retirada = models.DateTimeField(
        auto_now_add=True,            # server_default=func.now() — imutável após criação
        verbose_name='Data de retirada',
    )
    data_devolucao_prevista = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Prev. devolução',
    )
    data_devolucao_real = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Devolução real',
    )
    responsavel_entrega = models.CharField(
        max_length=100,
        verbose_name='Responsável pela entrega',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVA,
        db_index=True,                 # Indexado: filtrado com frequência
        verbose_name='Status',
    )
    observacoes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observações',
    )

    # ── Timestamp de criação ─────────────────────────────────
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    # ── Auditoria automática de campo ─────────────────────────
    history = HistoricalRecords()

    class Meta:
        verbose_name        = 'Cautela'
        verbose_name_plural = 'Cautelas'
        ordering            = ['-data_retirada']
        # db_table = 'cautelas'  # Descomente na etapa de migração de dados
        indexes = [
            models.Index(fields=['policial', 'status'], name='cautela_policial_status_idx'),
            models.Index(fields=['item', 'status'],     name='cautela_item_status_idx'),
            models.Index(fields=['status', 'data_devolucao_prevista'], name='cautela_atraso_idx'),
        ]

    def __str__(self) -> str:
        return f'Cautela #{self.pk} — {self.policial} | {self.item} [{self.status}]'

    @property
    def esta_em_atraso(self) -> bool:
        """True se ativa e data de devolução prevista já passou."""
        from django.utils import timezone
        return (
            self.status == self.Status.ATIVA
            and self.data_devolucao_prevista is not None
            and self.data_devolucao_prevista < timezone.now()
        )
