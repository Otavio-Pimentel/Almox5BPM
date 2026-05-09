from django.contrib import admin
from .models import Cautela

@admin.register(Cautela)
class CautelaAdmin(admin.ModelAdmin):
    list_display = ('id', 'policial', 'item', 'quantidade', 'status', 'data_retirada')
    list_filter = ('status',)
