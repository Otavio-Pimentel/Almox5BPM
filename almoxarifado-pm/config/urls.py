# config/urls.py
#
# Configuração de rotas REST com Django REST Framework.
#
# Endpoints automáticos gerados pelos ViewSets:
#
# AUTENTICAÇÃO:
#   POST   /auth/token/            → Obter JWT (login)
#   POST   /auth/token/refresh/    → Renovar JWT
#
# POLICIAIS (Efetivo):
#   GET    /policiais/             → Listar todos
#   POST   /policiais/             → Criar novo
#   GET    /policiais/{id}/        → Detalhe
#   PUT    /policiais/{id}/        → Atualizar
#   DELETE /policiais/{id}/        → Deletar (soft delete)
#   GET    /policiais/ativos/      → Apenas Ativo/Férias
#   GET    /policiais/{id}/cautelas_ativas/  → Cautelas do policial
#
# ITENS (Estoque):
#   GET    /itens/                 → Listar todos (com filtros)
#   POST   /itens/                 → Criar ou incrementar quantidade
#   GET    /itens/{id}/            → Detalhe
#   PUT    /itens/{id}/            → Atualizar
#   DELETE /itens/{id}/            → Deletar (se sem cautelas)
#   GET    /itens/disponiveis/     → Apenas em estoque e bom estado
#   GET    /itens/em_manutencao/   → Precisa manutenção
#   GET    /itens/{id}/historico_cautelas/  → Histórico de saídas
#
# CAUTELAS (Empréstimos):
#   GET    /cautelas/              → Listar todas
#   POST   /cautelas/              → Criar nova (status=Ativa)
#   GET    /cautelas/{id}/         → Detalhe
#   PUT    /cautelas/{id}/         → Editar observações
#   PUT    /cautelas/{id}/devolver → Devolver item (WHITELIST)
#   DELETE /cautelas/{id}/         → Deletar (se nunca saiu)
#   GET    /cautelas/ativas/       → Apenas Ativa
#   GET    /cautelas/em_atraso/    → Vencidas
#   GET    /cautelas/{id}/historico/ → Histórico de mudanças
#

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

# Importa os ViewSets (Etapa 2)
from apps.efetivo.views import PolicialViewSet
from apps.estoque.views import ItemViewSet
from apps.cautelas.views import CautelaViewSet

# Cria router automático (DefaultRouter gera browsable API + endpoints)
router = DefaultRouter()

# Registra os routers (gera URLs automáticas)
router.register(r'policiais', PolicialViewSet, basename='policial')
router.register(r'itens', ItemViewSet, basename='item')
router.register(r'cautelas', CautelaViewSet, basename='cautela')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Autenticação JWT
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API REST (ViewSets)
    path('api/', include(router.urls)),
    
    # Browsable API (DRF interface, remover em produção)
    path('api-auth/', include('rest_framework.urls')),
]

# Configuração do admin
admin.site.site_header = 'Almoxarifado PM — Administração'
admin.site.site_title = 'Admin'
admin.site.index_title = 'Bem-vindo ao Sistema'