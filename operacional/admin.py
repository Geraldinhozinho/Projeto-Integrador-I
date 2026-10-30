from django.contrib import admin
from .models import Bolsa, Bolsista, Agenda, Programa, Projeto, Supervisor, Vinculo_bolsista_bolsa, Setor  
# Register your models here.

    
@admin.register(Bolsista)
class BolsistaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'email', 'setor')

@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data', 'descricao', 'bolsista')
    
@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'email', 'setor')

@admin.register(Bolsa)
class BolsaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'carga_horaria_semanal', 'data_inicio', 'data_fim', 'setor', 'supervisor', 'ativo')
    list_filter = ('tipo', 'setor', 'ativo')
    search_fields = ('titulo', 'setor', 'supervisor__nome')
    
@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):  
    list_display = ('titulo', 'tipo', 'carga_horaria_semanal', 'data_inicio', 'data_fim', 'setor', 'supervisor', 'ativo', 'numero_edital')
    list_filter = ('tipo', 'setor', 'ativo')
    search_fields = ('titulo', 'setor', 'supervisor__nome')

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'carga_horaria_semanal', 'data_inicio', 'data_fim', 'setor', 'supervisor', 'ativo', 'titulo_projeto', 'objetivo', 'descricao', 'max_participantes_remunerados', 'max_participantes_nao_remunerados')
    list_filter = ('tipo', 'setor', 'ativo')
    search_fields = ('titulo', 'setor', 'supervisor__nome')
    
@admin.register(Vinculo_bolsista_bolsa)
class VinculoBolsistaBolsaAdmin(admin.ModelAdmin):
    list_display = ('bolsista', 'bolsa', 'remuneracao')
    list_filter = ('bolsa',)
    search_fields = ('bolsista__nome', 'bolsa__titulo')

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)