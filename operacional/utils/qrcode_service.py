import qrcode
from io import BytesIO
import base64
import hashlib
import time

SECRET_KEY = 'IFRN_PONTO_2026_SECRET'

def gerar_token_qr():
    # Janela de 60 segundos
    janela_tempo = int(time.time()) // 60 
    texto_base = f"{SECRET_KEY}_{janela_tempo}"
    return hashlib.sha256(texto_base.encode()).hexdigest()[:16]

def validar_token_qr(token_escaneado):
    if not token_escaneado:
        return False
    
    janela_atual = int(time.time()) // 60
    
    for offset in [0, -1]:
        janela_teste = janela_atual + offset
        texto_base = f"{SECRET_KEY}_{janela_teste}"
        token_esperado = hashlib.sha256(texto_base.encode()).hexdigest()[:16]
        
        if token_escaneado == token_esperado:
            return True
            
    return False

def gerar_imagem_qr(token):
    img = qrcode.make(token)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return qr_base64