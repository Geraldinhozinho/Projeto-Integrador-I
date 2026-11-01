from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from .models import Bolsa, Bolsista, Agenda, Frequencia, Justificativa, Historico

try:
    from .utils.qrcode_service import gerar_token_qr, validar_token_qr, gerar_imagem_qr
except ImportError:
    def gerar_token_qr(): return "TOKEN_TESTE"
    def validar_token_qr(t): return True
    def gerar_imagem_qr(t): return ""

def Index(request):
    return render(request, 'operacional/index.html')

def bolsistas(request):
    bolsistas_list = Bolsista.objects.all()
    return render(request, 'operacional/bolsistas.html', {'bolsistas': bolsistas_list})


def bolsas(request):
    bolsas_list = Bolsa.objects.all()
    return render(request, 'operacional/bolsas.html', {'bolsas': bolsas_list})


def agendas(request):
    agendas_list = Agenda.objects.all()
    return render(request, 'operacional/agendas.html', {'agendas': agendas_list})


def frequencia(request):
    if request.user.is_staff:
        frequencias = Frequencia.objects.select_related('bolsista').all()
    else:
        #ajustar conforome id do bolsista
        frequencias = Frequencia.objects.filter(bolsista__id=1)
    
    context = {
        'frequencias': frequencias.order_by('-data'),
        'user': request.user,
        'assinatura_disponivel': False, 
    }
    return render(request, 'operacional/frequencia.html', context)

def frequencia_supervisor(request):
    frequencias = Frequencia.objects.select_related('bolsista').order_by('-data')
    
    context = {
        'frequencias': frequencias,
        'bolsistas': Bolsista.objects.all()
    }
    return render(request, 'operacional/frequencia.html', context)


@require_POST
def registrar_entrada(request):
    bolsista_id = request.POST.get('bolsista_id')
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    
    freq = Frequencia()
    mensagem = freq.registrar_frequencia(bolsista)
    
    return redirect('frequencia')


@require_POST
def registrar_saida(request):
    bolsista_id = request.POST.get('bolsista_id')
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    
    freq = Frequencia()
    mensagem = freq.registrar_frequencia(bolsista)
    
    return redirect('frequencia')


def criar_justificativa(request, frequencia_pk=None):
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_final = request.POST.get('data_final')
        motivo = request.POST.get('motivo')
        informacao_complementar = request.POST.get('informacao_complementar', '')
        anexo = request.FILES.get('anexo')
        
        if frequencia_pk:
            frequencia = get_object_or_404(Frequencia, pk=frequencia_pk)
            bolsista = frequencia.bolsista
        else:
            bolsista = get_object_or_404(Bolsista, matricula=request.POST.get('matricula'))
            frequencia = None
        
        justificativa = Justificativa(
            bolsista=bolsista,
            frequencia=frequencia,
            data_inicio=data_inicio,
            data_final=data_final,
            motivo=motivo,
            informacao_complementar=informacao_complementar,
            status='PENDENTE'
        )
        
        if anexo:
            justificativa.anexo = anexo
        
        justificativa.cadastrar_justificativa()
        
        return redirect('frequencia')
    
    context = {
        'frequencia': get_object_or_404(Frequencia, pk=frequencia_pk) if frequencia_pk else None
    }
    return render(request, 'operacional/criar_justificativa.html', context)

def registrar_ponto_manual(request):
    if request.method == 'POST':
        bolsista_id = request.POST.get('bolsista_id')
        data = request.POST.get('data')
        hora_entrada = request.POST.get('hora_entrada')
        hora_saida = request.POST.get('hora_saida')
        justificativa = request.POST.get('justificativa')
        
        bolsista = get_object_or_404(Bolsista, id=bolsista_id)
        
        freq = Frequencia.objects.create(
            bolsista=bolsista,
            data=data,
            hora_entrada=hora_entrada,
            hora_saida=hora_saida,
            status='CONCLUIDA',
            observacao=justificativa
        )
        
        if justificativa:
            Historico.objects.create(
                frequencia=freq,
                usuario_responsavel='Supervisor',
                alteracao=f'Registro manual: entrada {hora_entrada}, saída {hora_saida}. Motivo: {justificativa}'
            )
        
        return redirect('frequencia')
    
    return render(request, 'operacional/registrar_ponto_manual.html', {
        'bolsistas': Bolsista.objects.all()
    })


def monitor_qrcode(request):
    """Exibe o QR Code na tela da COADE"""
    token = gerar_token_qr()
    qr_base64 = gerar_imagem_qr(token)
    
    return render(request, 'operacional/monitor_qrcode.html', {
        'qr_base64': qr_base64,
        'token': token
    })

@require_POST
def registrar_ponto_qr(request):
    try:
        data = json.loads(request.body)
        token = data.get('token')
        matricula = str(data.get('matricula', '')).strip()

        if not validar_token_qr(token):
            return JsonResponse({'sucesso': False, 'mensagem': 'QR Code expirado ou inválido.'}, status=400)

        bolsista = Bolsista.objects.get(matricula=matricula)
        
        freq = Frequencia()
        freq_obj, mensagem = freq.registrar_frequencia(bolsista, token) 

        if freq_obj is None:
            return JsonResponse({'sucesso': False, 'mensagem': mensagem}, status=400)

        return JsonResponse({
            'sucesso': True,
            'mensagem': mensagem,
            'bolsista': bolsista.nome,
            'status': freq_obj.status
        })

    except Bolsista.DoesNotExist:
        return JsonResponse({'sucesso': False, 'mensagem': 'Matrícula não encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro: {str(e)}'}, status=500)