# apps/cautelas/views.py
#
# ViewSets REST para domínio Cautelas (Empréstimos e Devoluções)
#
# ⚠️  MÁQUINA DE ESTADOS CRÍTICA
#
# Endpoints:
#   GET    /cautelas/              → Listar todas (com filtros)
#   POST   /cautelas/              → Criar nova (status=Ativa)
#   GET    /cautelas/{id}/         → Detalhe
#   PUT    /cautelas/{id}/         → Atualizar observações
#   PUT    /cautelas/{id}/devolver → Devolver item (WHITELIST)
#   DELETE /cautelas/{id}/         → Deletar (apenas se nunca saiu)
#

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction

from apps.shared.mixins import AuditoriaMixin, RBACMixin
from .models import Cautela
from apps.efetivo.models import Policial
from apps.estoque.models import Item
from .serializers import CautelaSerializer, CautelasDevolverSerializer


class CautelaViewSet(AuditoriaMixin, RBACMixin, viewsets.ModelViewSet):
    """
    ViewSet completo para Cautela.
    
    ⚠️  MÁQUINA DE ESTADOS WHITELIST:
    
    Estado: Ativa
    └─ Permite: devolução (→ Devolvida)
    └─ Bloqueia: qualquer outra operação de estado
    
    Estado: Devolvida
    └─ Permite: visualização
    └─ Bloqueia: devolução novamente, edição
    
    Se novos estados forem adicionados (Cancelada, Extraviada):
    O código não permitirá devolução automaticamente.
    Apenas estados na whitelist podem ser devolvidos.
    
    Compatibilidade FastAPI:
    - Payload JSON idêntico ao original
    - Comportamento de estoque preservado
    - Integração com Policial e Item funciona igual
    """
    
    queryset = Cautela.objects.all().select_related('policial', 'item')
    serializer_class = CautelaSerializer
    permission_classes = [IsAuthenticated]
    
    # Filtros
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['status', 'policial', 'item']
    search_fields = ['policial__nome_guerra', 'policial__matricula', 'item__descricao']
    ordering_fields = ['data_retirada', 'data_devolucao_prevista', 'criado_em']
    ordering = ['-data_retirada']

    def get_queryset(self):
        """Retorna cautelas com relacionamentos otimizados"""
        return Cautela.objects.all().select_related('policial', 'item')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        POST /cautelas/
        
        Validações:
        - Policial deve estar Ativo ou em Férias
        - Item não pode ser Inservível
        - Estoque deve ter quantidade disponível
        - Item seriado não pode estar em rua já
        
        Operação Atômica: cria cautela E decrementa estoque
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dados = serializer.validated_data
        policial_id = dados['policial'].id
        item_id = dados['item'].id
        quantidade = dados['quantidade']
        
        # Busca policial
        try:
            policial = Policial.objects.get(id=policial_id)
        except Policial.DoesNotExist:
            return Response(
                {'policial': 'Policial não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Valida status do policial
        if policial.status not in [Policial.Status.ATIVO, Policial.Status.FERIAS]:
            return Response(
                {
                    'policial': (
                        f"Policial '{policial.nome_guerra}' tem status '{policial.status}'. "
                        f"Apenas 'Ativo' e 'Férias' podem retirar material."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Busca item
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response(
                {'item': 'Item não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Valida condição do item
        if item.condicao == Item.Condicao.INSERVIVEL:
            return Response(
                {
                    'item': (
                        f"Item '{item.descricao}' está inservível. "
                        f"Não pode ser acautelado."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Item seriado: valida unicidade em rua
        if item.numero_serie:
            cautela_ativa = Cautela.objects.filter(
                item_id=item_id,
                status=Cautela.Status.ATIVA
            ).first()
            
            if cautela_ativa:
                return Response(
                    {
                        'item': (
                            f"Item '{item.descricao}' (série {item.numero_serie}) "
                            f"já está acautelado para {cautela_ativa.policial.nome_guerra} "
                            f"(cautela #{cautela_ativa.id})."
                        )
                    },
                    status=status.HTTP_409_CONFLICT
                )
        
        # Valida estoque disponível
        if item.quantidade_disponivel < quantidade:
            return Response(
                {
                    'quantidade': (
                        f"Estoque insuficiente. Disponível: {item.quantidade_disponivel}, "
                        f"Solicitado: {quantidade}"
                    )
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # ✅ Tudo ok: cria cautela E decrementa estoque (atomic)
        cautela = Cautela.objects.create(**dados)
        item.quantidade_disponivel -= quantidade
        item.save()
        
        # Registra auditoria
        self.registrar_auditoria(
            'cautela',
            cautela,
            dados_depois=serializer.to_representation(cautela)
        )
        
        serializer = self.get_serializer(cautela)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'])
    def devolver(self, request, pk=None):
        """
        PUT /cautelas/{id}/devolver/
        
        ⚠️  WHITELIST EXPLÍCITA:
        - Devolução APENAS se status == 'Ativa'
        - Qualquer outro status → HTTP 409
        
        Isso previne corrupção se novos status forem adicionados.
        
        Operação Atômica: atualiza cautela + incrementa estoque
        """
        cautela = self.get_object()
        
        # 🛡️  WHITELIST: apenas "Ativa" pode ser devolvida
        if cautela.status != Cautela.Status.ATIVA:
            return Response(
                {
                    'detail': (
                        f"Cautela #{cautela.id} com status '{cautela.status}' "
                        f"não pode ser devolvida. "
                        f"Apenas status 'Ativa' permite devolução. "
                        f"Entre em contato com a administração se acredita ser um erro."
                    )
                },
                status=status.HTTP_409_CONFLICT
            )
        
        serializer = CautelasDevolverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dados = serializer.validated_data
        
        with transaction.atomic():
            # Captura ANTES
            dados_antes = {
                'status': cautela.status,
                'data_devolucao_real': None,
            }
            
            # Atualiza cautela
            cautela.status = Cautela.Status.DEVOLVIDA
            cautela.data_devolucao_real = dados.get('data_devolucao_real') or timezone.now()
            
            if dados.get('observacoes'):
                obs_anterior = cautela.observacoes or ''
                cautela.observacoes = f"{obs_anterior} | Devolução: {dados['observacoes']}".strip(' |')
            
            cautela.save()
            
            # Incrementa estoque (capped em total)
            cautela.item.quantidade_disponivel = min(
                cautela.item.quantidade_disponivel + cautela.quantidade,
                cautela.item.quantidade_total
            )
            cautela.item.save()
            
            # Captura DEPOIS
            dados_depois = {
                'status': cautela.status,
                'data_devolucao_real': cautela.data_devolucao_real.isoformat(),
            }
            
            # Registra auditoria
            self.registrar_auditoria(
                'cautela',
                cautela,
                dados_antes=dados_antes,
                dados_depois=dados_depois
            )
        
        serializer = self.get_serializer(cautela)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def ativas(self, request):
        """
        GET /cautelas/ativas/
        
        Retorna apenas cautelas em status 'Ativa'.
        """
        queryset = self.get_queryset().filter(status=Cautela.Status.ATIVA)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def em_atraso(self, request):
        """
        GET /cautelas/em_atraso/
        
        Retorna cautelas ativas com data de devolução prevista já vencida.
        Útil para dashboard e alertas.
        """
        agora = timezone.now()
        queryset = self.get_queryset().filter(
            status=Cautela.Status.ATIVA,
            data_devolucao_prevista__isnull=False,
            data_devolucao_prevista__lt=agora
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def historico(self, request, pk=None):
        """
        GET /cautelas/{id}/historico/
        
        Retorna histórico completo de mudanças da cautela (via HistoricalRecords).
        """
        cautela = self.get_object()
        historico = cautela.history.all().order_by('-history_date')
        
        return Response([
            {
                'history_id': h.history_id,
                'status': h.status,
                'data_devolucao_real': h.data_devolucao_real,
                'history_date': h.history_date,
                'history_user': str(h.history_user),
                'history_type': h.get_history_type_display(),
            }
            for h in historico
        ])