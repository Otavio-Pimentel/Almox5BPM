import os

admins = {
    'core': '''from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPM, Auditoria

admin.site.register(UsuarioPM, UserAdmin)
@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acao', 'tabela_afetada', 'data_hora')
    list_filter = ('acao', 'tabela_afetada')
''',

    'efetivo': '''from django.contrib import admin
from .models import Policial

@admin.register(Policial)
class PolicialAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'nome_guerra', 'posto_graduacao', 'status')
    search_fields = ('matricula', 'nome_guerra')
    list_filter = ('status', 'posto_graduacao')
''',

    'estoque': '''from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo_material', 'quantidade_disponivel', 'condicao')
    search_fields = ('descricao', 'numero_serie')
    list_filter = ('tipo_material', 'condicao')
''',

    'cautelas': '''from django.contrib import admin
from .models import Cautela

@admin.register(Cautela)
class CautelaAdmin(admin.ModelAdmin):
    list_display = ('id', 'policial', 'item', 'quantidade', 'status', 'data_retirada')
    list_filter = ('status',)
'''
}

for app, content in admins.items():
    with open(f'apps/{app}/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)

print("✅ Painéis de administração configurados com sucesso!")