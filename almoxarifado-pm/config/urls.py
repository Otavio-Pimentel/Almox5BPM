# config/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

# 🌐 IMPORTAÇÕES DO FRONTEND
from frontend import views as frontend_views

# ⚙️ IMPORTAÇÕES DO BACKEND
from apps.efetivo.views import PolicialViewSet
from apps.estoque.views import ItemViewSet
from apps.cautelas.views import CautelaViewSet
from apps.core.views import DashboardStatsView

# Cria router automático
router = DefaultRouter()
router.register(r'policiais', PolicialViewSet, basename='policial')
router.register(r'itens', ItemViewSet, basename='item')
router.register(r'cautelas', CautelaViewSet, basename='cautela')

urlpatterns = [
    # ==========================================
    # 🌐 ROTAS DO FRONTEND (Telas HTML)
    # ==========================================
    path('', frontend_views.index, name='index'),
    path('login/', frontend_views.login, name='login'),
    path('cautelas/', frontend_views.cautelas, name='cautelas'),
    path('estoque/', frontend_views.estoque, name='estoque'),
    path('efetivo/', frontend_views.efetivo, name='efetivo'),
    
    # ==========================================
    # ⚙️ ROTAS DO BACKEND (API e Administração)
    # ==========================================
    path('admin/', admin.site.urls),
    
    # Autenticação JWT
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Dashboard Stats (Rota específica para os números do painel)
    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    
    # API REST (ViewSets automáticos)
    path('api/', include(router.urls)),
    
    # Interface navegável da API (DRF)
    path('api-auth/', include('rest_framework.urls')),
]

# Configuração visual do admin
admin.site.site_header = 'Almoxarifado PM — Administração'
admin.site.site_title = 'Admin'
admin.site.index_title = 'Bem-vindo ao Sistema'