from django.contrib import admin
from .models import Bolsa, Bolsista, Agenda
# Register your models here.

@admin.register(Bolsa)
class BolsaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'carga_horaria_semanal', 'remuneracao', 'data_inicio', 'data_fim', 'bolsista')
@admin.register(Bolsista)
class BolsistaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'email', 'setor')

@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data', 'descricao', 'bolsista')