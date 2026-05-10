from apps.core.models import Auditoria
from django.core.exceptions import PermissionDenied

class AuditoriaMixin:
    def registrar_auditoria(self, tabela, instancia, dados_antes=None, dados_depois=None):
        Auditoria.objects.create(
            usuario=self.request.user,
            acao=f'Alteração em {tabela}',
            tabela_afetada=tabela,
            registro_id=instancia.id,
            dados_anteriores=str(dados_antes) if dados_antes else None,
            dados_novos=str(dados_depois) if dados_depois else None,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT')
        )

class RBACMixin:
    def check_permissions(self, request):
        super().check_permissions(request)
        pass
