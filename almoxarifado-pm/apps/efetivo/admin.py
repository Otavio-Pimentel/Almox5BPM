from django.contrib import admin
from .models import Policial

@admin.register(Policial)
class PolicialAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'nome_guerra', 'posto_graduacao', 'status')
    search_fields = ('matricula', 'nome_guerra')
    list_filter = ('status', 'posto_graduacao')
