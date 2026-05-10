# apps/estoque/views.py
#
# ViewSets REST para domínio Estoque (Itens)
#
# ⚠️  LÓGICA CRÍTICA: Seriado vs Genérico
#
# Endpoints:
#   GET    /itens/                 → Listar todos (com filtros)
#   POST   /itens/                 → Criar ou incrementar
#   GET    /itens/{id}/            → Detalhe
#   PUT    /itens/{id}/            → Atualizar
#   DELETE /itens/{id}/            → Deletar (apenas admin, se sem cautelas)
#

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.shared.mixins import AuditoriaMixin, RBACMixin
from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(AuditoriaMixin, RBACMixin, viewsets.ModelViewSet):
    """
    ViewSet completo para Item.
    
    COMPORTAMENTO ESPECIAL (Lógica de Negócio):
    
    1️⃣  ITEM SERIADO (numero_serie preenchido)
        ├─ Exemplos: arma, rádio HT, colete balístico
        ├─ Série ÚNICA (409 se tentar duplicar)
        ├─ Sempre cria NOVA linha
        └─ Uma cautela por item físico
    
    2️⃣  ITEM GENÉRICO (numero_serie = null)
        ├─ Exemplos: munição, tonfa, fardamento
        ├─ Controlado por QUANTIDADE
        ├─ Se existe (tipo + descrição) → incrementa quantidade
        ├─ Se não existe → cria nova linha
        └─ Múltiplas cautelas simultâneas (até esgotar estoque)
    
    Compatibilidade FastAPI:
    - Payload JSON idêntico ao original
    - Comportamento de incremento preservado
    """
    
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    
    # Filtros
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['tipo_material', 'condicao']
    search_fields = ['descricao', 'numero_serie', 'localizacao']
    ordering_fields = ['tipo_material', 'descricao', 'criado_em']
    ordering = ['tipo_material', 'descricao']

    def create(self, request, *args, **kwargs):
        """
        POST /itens/
        
        ⚠️  LÓGICA CRÍTICA: Seriado vs Genérico
        
        CASO 1: numero_serie presente (SERIADO)
            → Valida unicidade de série
            → Cria NOVA linha sempre
            → Erro 409 se série duplicada
        
        CASO 2: numero_serie vazio/null (GENÉRICO)
            → Busca item idêntico (tipo_material + descricao)
            → Se existe: INCREMENTA quantidade (não cria linha)
            → Se não existe: cria nova linha
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dados = serializer.validated_data
        numero_serie = dados.get('numero_serie')
        
        # ─────────────────────────────────────────────────────
        # CASO 1: ITEM SERIADO
        # ─────────────────────────────────────────────────────
        if numero_serie:
            serie_norm = numero_serie.upper().strip()
            
            # Verifica unicidade
            if Item.objects.filter(numero_serie=serie_norm).exists():
                return Response(
                    {
                        'numero_serie': [
                            f"Série '{serie_norm}' já existe no estoque."
                        ]
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            # Cria nova linha para seriado
            item = Item.objects.create(**dados)
            
            # Registra auditoria
            self.registrar_auditoria(
                'item',
                item,
                dados_depois=serializer.data
            )
            
            serializer = self.get_serializer(item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # ─────────────────────────────────────────────────────
        # CASO 2: ITEM GENÉRICO (sem série)
        # ─────────────────────────────────────────────────────
        else:
            # Busca item idêntico
            item_existente = Item.objects.filter(
                numero_serie__isnull=True,
                tipo_material=dados['tipo_material'],
                descricao=dados['descricao'],
            ).first()
            
            if item_existente:
                # ✔️ Item existe → INCREMENTA quantidade
                qtd_total_antes = item_existente.quantidade_total
                qtd_disp_antes = item_existente.quantidade_disponivel
                
                item_existente.quantidade_total += dados['quantidade_total']
                item_existente.quantidade_disponivel += dados['quantidade_disponivel']
                item_existente.save()
                
                # Registra auditoria
                self.registrar_auditoria(
                    'item',
                    item_existente,
                    dados_antes={
                        'quantidade_total': qtd_total_antes,
                        'quantidade_disponivel': qtd_disp_antes,
                    },
                    dados_depois={
                        'quantidade_total': item_existente.quantidade_total,
                        'quantidade_disponivel': item_existente.quantidade_disponivel,
                    }
                )
                
                serializer = self.get_serializer(item_existente)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            else:
                # ✗ Item não existe → CRIA nova linha
                item = Item.objects.create(**dados)
                
                # Registra auditoria
                self.registrar_auditoria(
                    'item',
                    item,
                    dados_depois=serializer.data
                )
                
                serializer = self.get_serializer(item)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /itens/{id}
        
        Bloqueia se há cautelas vinculadas (histórico de uso).
        Admin pode deletar apenas itens sem movimento.
        """
        item = self.get_object()
        
        # Verifica se tem cautelas
        if item.cautelas.exists():
            return Response(
                {
                    'detail': f"Item '{item.descricao}' tem {item.cautelas.count()} "
                              f"cautela(s) vinculada(s). Não pode ser deletado."
                },
                status=status.HTTP_409_CONFLICT
            )
        
        self.perform_destroy(item)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        """
        GET /itens/disponiveis/
        
        Retorna itens com estoque e em bom estado.
        """
        queryset = self.get_queryset().filter(
            quantidade_disponivel__gt=0,
            condicao__in=[Item.Condicao.NOVO, Item.Condicao.BOM]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def em_manutencao(self, request):
        """
        GET /itens/em_manutencao/
        
        Retorna itens que precisam de manutenção.
        """
        queryset = self.get_queryset().filter(
            condicao=Item.Condicao.MANUTENCAO
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def historico_cautelas(self, request, pk=None):
        """
        GET /itens/{id}/historico_cautelas/
        
        Retorna todas as cautelas (ativas e devolvidas) do item.
        """
        item = self.get_object()
        cautelas = item.cautelas.all().order_by('-data_retirada')
        
        from apps.cautelas.serializers import CautelaSerializer
        serializer = CautelaSerializer(cautelas, many=True)
        return Response(serializer.data)