# apps/efetivo/views.py
#
# ViewSets REST para domínio Efetivo (Policiais)
#
# Endpoints:
#   GET    /policiais/             → Listar todos
#   POST   /policiais/             → Criar novo
#   GET    /policiais/{id}/        → Detalhe
#   PUT    /policiais/{id}/        → Atualizar
#   DELETE /policiais/{id}/        → Deletar (soft delete via status)
#

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.shared.mixins import AuditoriaMixin, RBACMixin
from .models import Policial
from .serializers import PolicialSerializer


class PolicialViewSet(AuditoriaMixin, RBACMixin, viewsets.ModelViewSet):
    """
    ViewSet completo para Policial.
    
    CRUD + Auditoria automática via AuditoriaMixin.
    
    Features:
    - GET com filtros (status, posto, search por matrícula/nome)
    - POST com validação de campos
    - PUT com histórico automático (HistoricalRecords)
    - DELETE soft-delete via status (nunca exclui fisicamente)
    - Auditoria registrada em toda ação (quem, o quê, quando, IP)
    
    Compatibilidade FastAPI:
    - Payload JSON idêntico ao FastAPI original
    - Comportamento de campos mantido
    - Enums replicados com exatidão
    """
    
    queryset = Policial.objects.all()
    serializer_class = PolicialSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['status', 'posto_graduacao']
    search_fields = ['matricula', 'nome_guerra', 'nome_completo']
    ordering_fields = ['matricula', 'nome_guerra', 'posto_graduacao', 'criado_em']
    ordering = ['nome_guerra']
    
    def get_queryset(self):
        """
        Filtra por query params (RBAC futuro com django-guardian).
        
        Para Etapa 1-2: retorna todos os dados.
        Etapa 3: será filtrado por setor/unidade do usuário.
        """
        return Policial.objects.all()

    def destroy(self, request, *args, **kwargs):
        """
        Override de DELETE: soft-delete via status.
        
        Nunca deleta fisicamente. Marca como Inativo.
        """
        policial = self.get_object()
        
        if policial.cautelas.filter(status='Ativa').exists():
            return Response(
                {
                    'detail': f"Policial '{policial.nome_guerra}' tem cautelas ativas. "
                              "Não pode ser removido."
                },
                status=status.HTTP_409_CONFLICT
            )
        
        policial.status = Policial.Status.INATIVO
        policial.save()
        
        self.registrar_auditoria(
            'policial',
            policial,
            dados_antes={'status': 'Ativo'},
            dados_depois={'status': 'Inativo'}
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def ativos(self, request):
        """
        GET /policiais/ativos/
        
        Retorna apenas policiais com status Ativo ou Férias.
        """
        queryset = self.get_queryset().filter(
            status__in=[Policial.Status.ATIVO, Policial.Status.FERIAS]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def cautelas_ativas(self, request, pk=None):
        """
        GET /policiais/{id}/cautelas_ativas/
        
        Retorna cautelas ativas do policial.
        """
        policial = self.get_object()
        cautelas = policial.cautelas.filter(status='Ativa').order_by('-data_retirada')
        
        from apps.cautelas.serializers import CautelaSerializer
        serializer = CautelaSerializer(cautelas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def cautelas_ativas(self, request, pk=None):
        """
        GET /policiais/{id}/cautelas_ativas/
        
        Retorna cautelas ativas do policial.
        """
        policial = self.get_object()
        cautelas = policial.cautelas.filter(status='Ativa').order_by('-data_retirada')
        
        from apps.cautelas.serializers import CautelaSerializer
        serializer = CautelaSerializer(cautelas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='matricula/(?P<matricula>[^/.]+)')
    def buscar_por_matricula(self, request, matricula=None):
        """
        GET /api/policiais/matricula/12345/
        
        Custom endpoint para encontrar policial pela matrícula (Leitor de Código de Barras).
        """
        try:
            policial = self.get_queryset().get(matricula=matricula)
            serializer = self.get_serializer(policial)
            return Response(serializer.data)
        except Policial.DoesNotExist:
            return Response(
                {'detail': f'Policial com matrícula "{matricula}" não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )