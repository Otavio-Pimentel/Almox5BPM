from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo_material', 'quantidade_disponivel', 'condicao')
    search_fields = ('descricao', 'numero_serie')
    list_filter = ('tipo_material', 'condicao')
