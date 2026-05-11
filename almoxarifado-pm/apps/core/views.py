from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from apps.efetivo.models import Policial
from apps.estoque.models import Item
from apps.cautelas.models import Cautela

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoje = timezone.now()
        
        return Response({
            "cautelas_ativas": Cautela.objects.filter(status='Ativa').count(),
            "cautelas_em_atraso": Cautela.objects.filter(
                status='Ativa', 
                data_devolucao_prevista__lt=hoje
            ).count(),
            "itens_em_manutencao": Item.objects.filter(condicao='Precisa de Manutenção').count(),
            "itens_disponiveis": Item.objects.filter(quantidade_disponivel__gt=0).count(),
            "total_itens": Item.objects.count(),
            "policiais_ativos": Policial.objects.filter(status='Ativo').count(),
        })