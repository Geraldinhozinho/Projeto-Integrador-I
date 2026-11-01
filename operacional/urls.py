from django.urls import path
from .views import (
    Index, bolsas, bolsistas, agendas, frequencia, frequencia_supervisor, 
    registrar_entrada, registrar_saida, criar_justificativa, registrar_ponto_manual,
    monitor_qrcode, registrar_ponto_qr 
)

urlpatterns = [
    path('', Index, name='index'),
    path('bolsas/', bolsas, name='bolsas'),
    path('bolsistas/', bolsistas, name='bolsistas'),
    path('agendas/', agendas, name='agendas'),
    
    # Frequência
    path('frequencia/', frequencia, name='frequencia'),
    path('frequencia/supervisor/', frequencia_supervisor, name='frequencia_supervisor'),
    
    # Ações de Ponto
    path('frequencia/entrada/', registrar_entrada, name='registrar_entrada'),
    path('frequencia/saida/', registrar_saida, name='registrar_saida'),
    path('frequencia/manual/', registrar_ponto_manual, name='registrar_ponto_manual'),
    path('frequencia/<int:frequencia_pk>/justificativa/', criar_justificativa, name='criar_justificativa'),
    
    # QR Code (NOVO)
    path('monitor/qrcode/', monitor_qrcode, name='monitor_qrcode'),
    path('frequencia/registrar-qr/', registrar_ponto_qr, name='registrar_ponto_qr'),
]