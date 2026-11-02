from django.urls import path
from .views import (Index, bolsas, bolsistas, agendas, frequencia, frequencia_supervisor, registrar_entrada, registrar_saida, criar_justificativa, 
            monitor_qrcode, registrar_ponto_qr, ver_justificativa, frequencia_bolsista_especifico, meus_bolsistas, registrar_ponto_manual, comprovantes_mensais, relatorio_frequencia)

urlpatterns = [
    path('', Index, name='index'),
    path('bolsas/', bolsas, name='bolsas'),
    path('bolsistas/', bolsistas, name='bolsistas'),
    path('agendas/', agendas, name='agendas'),
    
    path('frequencia/', frequencia, name='frequencia'),
    path('frequencia/supervisor/', frequencia_supervisor, name='frequencia_supervisor'),
    
    path('frequencia/entrada/', registrar_entrada, name='registrar_entrada'),
    path('frequencia/saida/', registrar_saida, name='registrar_saida'),
    path('frequencia/<int:bolsista_id>/', frequencia_bolsista_especifico, name='frequencia_bolsista'),
    path('frequencia/<int:frequencia_pk>/justificativa/', criar_justificativa, name='criar_justificativa'),
    path('frequencia/<int:frequencia_pk>/ver_justificativa/', ver_justificativa, name='ver_justificativa'),
    
    path('supervisor/ponto_manual/', registrar_ponto_manual, name='registrar_ponto_manual'),
    path('supervisor/meus_bolsistas/', meus_bolsistas, name='meus_bolsistas'),
    
    path('monitor/qrcode/', monitor_qrcode, name='monitor_qrcode'),
    path('frequencia/registrar_qr/', registrar_ponto_qr, name='registrar_ponto_qr'),

    path('comprovantes-mensais/', comprovantes_mensais, name='comprovantes_mensais'),
    path(
        'relatorio-frequencia/<int:ano>/<int:mes>/',
        relatorio_frequencia,
        name='relatorio_frequencia'
    ),
]