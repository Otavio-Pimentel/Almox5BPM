from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPM, Auditoria

admin.site.register(UsuarioPM, UserAdmin)
@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acao', 'tabela_afetada', 'data_hora')
    list_filter = ('acao', 'tabela_afetada')
