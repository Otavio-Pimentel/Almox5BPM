# apps/core/models.py
#
# Modelos de infraestrutura do sistema:
#   - UsuarioPM  → modelo de usuário customizado (AbstractUser)
#   - Auditoria  → trilha forense de ações operacionais
#
# Dependências externas obrigatórias:
#   pip install django-simple-history
#
# Configuração obrigatória em settings.py:
#   AUTH_USER_MODEL = 'core.UsuarioPM'
#   INSTALLED_APPS  = [..., 'simple_history', 'core', ...]
#   MIDDLEWARE      = [..., 'simple_history.middleware.HistoryRequestMiddleware']
#
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords


# ─────────────────────────────────────────────────────────────
# USUÁRIO DO SISTEMA
# ─────────────────────────────────────────────────────────────
class UsuarioPM(AbstractUser):
    """
    Modelo de usuário principal do sistema.

    Herda de AbstractUser:
        username, password (bcrypt nativo), email,
        first_name, last_name, is_staff, is_active,
        is_superuser, last_login, date_joined,
        groups, user_permissions.

    Adiciona campos específicos da PM:
        papel, unidade.

    Por que AbstractUser e não AbstractBaseUser:
        AbstractBaseUser exige reimplementar todo o auth pipeline.
        AbstractUser mantém compatibilidade total com Django Admin,
        DRF TokenAuth, django-guardian e django-simple-history.
        Só escolha AbstractBaseUser se o mecanismo de login for
        radicalmente diferente (ex: login por CPF sem username).
    """

    class Papel(models.TextChoices):
        ADMIN    = 'admin',    'Administrador (Oficial)'
        OPERADOR = 'operador', 'Operador (Sgt / Almoxarife)'
        LEITURA  = 'leitura',  'Consulta (Sd / Cb)'

    papel = models.CharField(
        max_length=20,
        choices=Papel.choices,
        default=Papel.LEITURA,
        verbose_name='Papel de acesso',
        help_text='Define o nível de permissão no sistema.',
    )
    unidade = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Unidade / Companhia',
        help_text='Ex: 1ª CIA, 2º PEL. Usado para controle futuro de acesso por setor.',
    )

    # Auditoria automática — registra toda alteração neste model
    history = HistoricalRecords()

    class Meta:
        verbose_name        = 'Usuário PM'
        verbose_name_plural = 'Usuários PM'
        # db_table = 'usuarios'
        # ↑ Descomente APENAS na etapa de migração de dados,
        #   para apontar para a tabela existente do FastAPI.
        #   Em projeto novo, mantenha comentado (Django cria 'core_usuariopm').

    def __str__(self) -> str:
        return f'{self.get_papel_display()} — {self.username}'

    @property
    def is_admin(self) -> bool:
        return self.papel == self.Papel.ADMIN

    @property
    def is_operador(self) -> bool:
        return self.papel in (self.Papel.ADMIN, self.Papel.OPERADOR)


# ─────────────────────────────────────────────────────────────
# AUDITORIA FORENSE
# ─────────────────────────────────────────────────────────────
class Auditoria(models.Model):
    """
    Trilha de auditoria forense de ações operacionais.

    Registra eventos de negócio com semântica explícita:
        criar_cautela, devolver_item, criar_item, etc.

    Complementa (não substitui) o django-simple-history:
        - simple_history  → captura TODA alteração de campo automaticamente
        - Auditoria       → captura eventos de negócio com contexto IP/UserAgent

    Imutabilidade: Esta tabela nunca deve receber UPDATE ou DELETE.
    O campo on_delete=PROTECT no usuario garante rastreabilidade mesmo
    se o usuário for inativado.
    """

    class Acao(models.TextChoices):
        CRIAR_CAUTELA      = 'criar_cautela',      'Criar Cautela'
        DEVOLVER_ITEM      = 'devolver_item',       'Devolver Item'
        CRIAR_ITEM         = 'criar_item',          'Criar Item'
        ALTERAR_ITEM       = 'alterar_item',        'Alterar Item'
        DELETAR_ITEM       = 'deletar_item',        'Deletar Item'
        CRIAR_POLICIAL     = 'criar_policial',      'Criar Policial'
        ALTERAR_POLICIAL   = 'alterar_policial',    'Alterar Policial'
        DELETAR_POLICIAL   = 'deletar_policial',    'Deletar Policial'
        ALTERAR_SENHA      = 'alterar_senha',       'Alterar Senha'
        CRIAR_USUARIO      = 'criar_usuario',       'Criar Usuário'
        DELETAR_USUARIO    = 'deletar_usuario',     'Deletar Usuário'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,          # Nunca apaga usuário com histórico
        related_name='acoes_auditoria',
        verbose_name='Operador',
        db_index=True,
    )
    acao = models.CharField(
        max_length=50,
        choices=Acao.choices,
        db_index=True,
        verbose_name='Ação',
    )
    tabela_afetada = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='Tabela afetada',
    )
    registro_id = models.PositiveIntegerField(
        db_index=True,
        verbose_name='ID do registro afetado',
    )
    dados_anteriores = models.TextField(
        null=True,
        blank=True,
        verbose_name='Snapshot anterior (JSON)',
    )
    dados_novos = models.TextField(
        null=True,
        blank=True,
        verbose_name='Snapshot posterior (JSON)',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        protocol='both',           # Aceita IPv4 e IPv6
        verbose_name='IP de origem',
    )
    user_agent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='User-Agent',
    )
    data_hora = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Data/hora UTC',
    )

    class Meta:
        verbose_name        = 'Registro de Auditoria'
        verbose_name_plural = 'Registros de Auditoria'
        ordering            = ['-data_hora']
        # db_table = 'auditoria'  # Descomente na etapa de migração de dados

    def __str__(self) -> str:
        return f'[{self.data_hora:%d/%m/%Y %H:%M}] {self.usuario} → {self.acao} ({self.tabela_afetada}#{self.registro_id})'
