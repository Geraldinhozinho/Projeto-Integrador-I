from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Max
import json
import calendar
from datetime import date, datetime
from django.contrib import messages
from .models import Bolsa, Bolsista, Agenda, Frequencia, Justificativa, Historico, Supervisor

try:
    from .utils.qrcode_service import gerar_token_qr, validar_token_qr, gerar_imagem_qr
except ImportError:
    def gerar_token_qr(): return "TOKEN_TESTE"
    def validar_token_qr(t): return True
    def gerar_imagem_qr(t): return ""

def calcular_dias_uteis_mes(ano, mes):
    dias_uteis = 0
    cal = calendar.monthcalendar(ano, mes)
    for semana in cal:
        for dia in semana:
            if dia != 0: 
                data_obj = date(ano, mes, dia)
                if data_obj.weekday() < 5:  
                    dias_uteis += 1
    return dias_uteis

def preencher_dias_retroativos(bolsista_id, data_referencia):
    import calendar
    from datetime import date, timedelta
    
    ano = data_referencia.year
    mes = data_referencia.month
    ontem = data_referencia.date() - timedelta(days=1)
    
    dias_do_mes_passados = []
    cal = calendar.monthcalendar(ano, mes)
    for semana in cal:
        for dia in semana:
            if dia != 0:
                data_obj = date(ano, mes, dia)
                if data_obj <= ontem:
                    dias_do_mes_passados.append(data_obj)
    
    registros_existentes = Frequencia.objects.filter(
        bolsista_id=bolsista_id,
        data__in=dias_do_mes_passados
    ).values_list('data', flat=True)
    
    registros_criados = 0
    for dia in dias_do_mes_passados:
        if dia not in registros_existentes:
            if dia.weekday() < 5:
                status_dia = 'FALTA'
                obs_dia = 'Ausência não registrada (gerado automaticamente)'
            else:
                status_dia = 'FIM_DE_SEMANA'
                obs_dia = 'Fim de Semana'
                
            Frequencia.objects.create(
                bolsista_id=bolsista_id,
                data=dia,
                status=status_dia,
                observacao=obs_dia
            )
            registros_criados += 1
            
    return registros_criados
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
    bolsista_id = 1  
    hoje = timezone.localtime(timezone.now())
    primeiro_dia = hoje.replace(day=1, hour=0, minute=0, second=0)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1], hour=23, minute=59, second=59)
    intervalo_mes = [primeiro_dia.date(), ultimo_dia.date()]
    
    if request.user.is_staff:
        frequencias = Frequencia.objects.select_related('bolsista').filter(
            data__range=intervalo_mes
        ).order_by('-data', '-hora_entrada')
        ultima_frequencia = None
        resumo = {}
    else:
        preencher_dias_retroativos(bolsista_id, hoje)

        frequencias = Frequencia.objects.filter(
            bolsista__id=bolsista_id,
            data__range=intervalo_mes
        ).order_by('-data', '-hora_entrada')
        
        ultima_frequencia = frequencias.filter(status='EM_ABERTO').first()
        if not ultima_frequencia:
            ultima_frequencia = frequencias.first()
        
        dias_uteis_reais = calcular_dias_uteis_mes(hoje.year, hoje.month)
        
        resumo = {
            'dias_previstos': dias_uteis_reais,  
            'presencas': frequencias.filter(status='CONCLUIDA').count(),
            'faltas': frequencias.filter(status='FALTA').count(),
        }
    
    context = {
        'frequencias': frequencias,
        'user': request.user,
        'assinatura_disponivel': False,
        'ultima_frequencia': ultima_frequencia,
        'resumo': resumo,
    }
    return render(request, 'operacional/frequencia.html', context)

def frequencia_bolsista_especifico(request, bolsista_id):
    if not request.user.is_staff:
        return redirect('frequencia')
        
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    
    hoje = timezone.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
    intervalo_mes = [primeiro_dia.date(), ultimo_dia.date()]
    
    frequencias = Frequencia.objects.filter(
        bolsista=bolsista,
        data__range=intervalo_mes
    ).order_by('-data')
    
    ultima_frequencia = frequencias.first()
    
    dias_uteis_reais = calcular_dias_uteis_mes(hoje.year, hoje.month)
    
    resumo = {
        'dias_previstos': dias_uteis_reais,
        'presencas': frequencias.filter(status='CONCLUIDA').count(),
        'faltas': frequencias.filter(status='FALTA').count(),
    }

    context = {
        'frequencias': frequencias,
        'user': request.user,
        'assinatura_disponivel': False,
        'ultima_frequencia': ultima_frequencia,
        'resumo': resumo,
        'bolsista_selecionado': bolsista
    }
    return render(request, 'operacional/frequencia.html', context)



@require_POST
def registrar_entrada(request):
    bolsista_id = request.POST.get('bolsista_id')
    print(f"TENTANDO REGISTRAR ENTRADA - ID RECEBIDO: {bolsista_id}")
    
    try:
        bolsista = get_object_or_404(Bolsista, id=bolsista_id)
        
        freq = Frequencia()
        obj_retornado, mensagem = freq.registrar_frequencia(bolsista, token='') 
        
        if obj_retornado is None:
            print(f"ERRO: Token inválido ou já usado")
        else:
            print(f"SUCESSO: {mensagem} | Status: {obj_retornado.status}")
            
    except Exception as e:
        print(f"ERRO CRÍTICO AO SALVAR: {e}")
    
    return redirect('frequencia')


@require_POST
def registrar_saida(request):
    bolsista_id = request.POST.get('bolsista_id')
    print(f"TENTANDO REGISTRAR SAÍDA - ID RECEBIDO: {bolsista_id}")
    
    try:
        bolsista = get_object_or_404(Bolsista, id=bolsista_id)
        
        freq = Frequencia()
        obj_retornado, mensagem = freq.registrar_frequencia(bolsista, token='')
        
        if obj_retornado is None:
            print(f"ERRO: Registro já concluído ou token inválido")
        else:
            print(f"SUCESSO: {mensagem} | Status: {obj_retornado.status}")
            
    except Exception as e:
        print(f"ERRO CRÍTICO AO SALVAR: {e}")
        
    return redirect('frequencia')


def frequencia_supervisor(request):
    frequencias = Frequencia.objects.select_related('bolsista').order_by('-data')
    return render(request, 'operacional/frequencia.html', {
        'frequencias': frequencias,
        'bolsistas': Bolsista.objects.all(),
        'user': request.user,
        'assinatura_disponivel': False,
    })

def frequencia_bolsista_especifico(request, bolsista_id):
    if not request.user.is_staff:
        return redirect('frequencia')
        
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    frequencias = Frequencia.objects.filter(bolsista=bolsista).order_by('-data')
    
    ultima_frequencia = frequencias.first()
    
    hoje = timezone.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
    
    freq_mes = Frequencia.objects.filter(
        bolsista=bolsista,
        data__range=[primeiro_dia.date(), ultimo_dia.date()]
    )
    
    resumo = {
        'dias_previstos': 20, 
        'presencas': freq_mes.filter(status='CONCLUIDA').count(),
        'faltas': freq_mes.filter(status='FALTA').count(),
    }

    context = {
        'frequencias': frequencias,
        'user': request.user,
        'assinatura_disponivel': False,
        'ultima_frequencia': ultima_frequencia,
        'resumo': resumo,
        'bolsista_selecionado': bolsista 
    }
    return render(request, 'operacional/frequencia.html', context)

# def criar_justificativa(request, frequencia_pk=None):
#     if request.method == 'POST':
#         data_inicio = request.POST.get('data_inicio')
#         data_final = request.POST.get('data_final')
#         motivo = request.POST.get('motivo')
#         informacao_complementar = request.POST.get('informacao_complementar', '')
#         anexo = request.FILES.get('anexo')
        
#         if frequencia_pk:
#             frequencia = get_object_or_404(Frequencia, pk=frequencia_pk)
#             bolsista = frequencia.bolsista
#         else:
#             bolsista = get_object_or_404(Bolsista, matricula=request.POST.get('matricula'))
#             frequencia = None
        
#         justificativa = Justificativa(
#             bolsista=bolsista,
#             frequencia=frequencia,
#             data_inicio=data_inicio,
#             data_final=data_final,
#             motivo=motivo,
#             informacao_complementar=informacao_complementar,
#             status='PENDENTE'
#         )
        
#         if anexo:
#             justificativa.anexo = anexo
        
#         justificativa.cadastrar_justificativa()
        
#         return redirect('frequencia')
    
#     context = {
#         'frequencia': get_object_or_404(Frequencia, pk=frequencia_pk) if frequencia_pk else None
#     }
#     return render(request, 'operacional/criar_justificativa.html', context)

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
            bolsista = get_object_or_404(Bolsista, id=request.POST.get('bolsista_id'))
            frequencia = None
        
        # 👇 Pega o supervisor do setor do bolsista automaticamente
        supervisor = bolsista.setor.supervisores.first()
        
        if not supervisor:
            messages.error(request, 'Nenhum supervisor encontrado para o seu setor. Contate o administrativo.')
            return redirect('frequencia')
        
        justificativa = Justificativa(
            bolsista=bolsista,
            frequencia=frequencia,
            supervisor=supervisor,  # 👈 Preenchido automaticamente
            data_inicio=data_inicio,
            data_final=data_final,
            motivo=motivo,
            informacao_complementar=informacao_complementar,
            status='PENDENTE'
        )
        
        if anexo:
            justificativa.anexo = anexo
        
        justificativa.cadastrar_justificativa()
        messages.success(request, 'Justificativa enviada com sucesso para análise do supervisor.')
        
        return redirect('frequencia')
    
    # GET: exibe o formulário
    frequencia_obj = get_object_or_404(Frequencia, pk=frequencia_pk) if frequencia_pk else None
    context = {
        'frequencia': frequencia_obj,
    }
    return render(request, 'operacional/criar_justificativa.html', context)

def ver_justificativa(request, frequencia_pk):
    frequencia = get_object_or_404(Frequencia, pk=frequencia_pk)
    justificativa = frequencia.justificativa.first()
    
    if not justificativa:
        return redirect('frequencia')
    
    context = {
        'frequencia': frequencia,
        'justificativa': justificativa
    }
    return render(request, 'operacional/ver_justificativa.html', context)


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

def meus_bolsistas(request):
    if not request.user.is_staff:
        return redirect('index')
    
    bolsistas = Bolsista.objects.all().order_by('nome')
    
    hoje = timezone.localtime(timezone.now()).date()
    bolsistas_enriquecidos = []
    
    for bolsista in bolsistas:
        registro_hoje = Frequencia.objects.filter(
            bolsista=bolsista,
            data=hoje
        ).first()
        
        mes_atual = timezone.localtime(timezone.now())
        primeiro_dia = mes_atual.replace(day=1)
        ultimo_dia = mes_atual.replace(day=calendar.monthrange(mes_atual.year, mes_atual.month)[1])
        
        faltas_mes = Frequencia.objects.filter(
            bolsista=bolsista,
            data__range=[primeiro_dia.date(), ultimo_dia.date()],
            status='FALTA'
        ).count()
        
        justificativas_pendentes = Justificativa.objects.filter(
            bolsista=bolsista,
            status='PENDENTE'
        ).count()
        
        bolsistas_enriquecidos.append({
            'bolsista': bolsista,
            'registro_hoje': registro_hoje,
            'faltas_mes': faltas_mes,
            'justificativas_pendentes': justificativas_pendentes,
        })

    context = {
        'bolsistas_enriquecidos': bolsistas_enriquecidos,
        'total_bolsistas': len(bolsistas_enriquecidos),
    }
    return render(request, 'operacional/meus_bolsistas.html', context)

def registrar_ponto_manual(request):
    bolsista_id = request.GET.get('bolsista_id')
    bolsista_selecionado = None
    
    if bolsista_id:
        bolsista_selecionado = get_object_or_404(Bolsista, id=bolsista_id)
    
    if request.method == 'POST':
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG REGISTRO MANUAL")
        print(f"POST data: {request.POST}")
        
        post_bolsista_id = request.POST.get('bolsista_id')
        data_str = request.POST.get('data')
        horario_str = request.POST.get('horario')
        operacao = request.POST.get('operacao')
        observacao = request.POST.get('observacao', '')
        
        print(f"Bolsista ID do POST: {post_bolsista_id}")
        print(f"Data: {data_str}")
        print(f"Horário: {horario_str}")
        print(f"Operação: {operacao}")
        print(f"{'='*60}\n")
        
        if not post_bolsista_id:
            messages.error(request, 'Selecione um bolsista.')
            return render(request, 'operacional/registro_manual.html', {
                'bolsistas': Bolsista.objects.all().order_by('nome'),
                'hoje': timezone.now(),
            })
        
        bolsista_selecionado = get_object_or_404(Bolsista, id=post_bolsista_id)
        
        if not (data_str and horario_str and operacao):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return render(request, 'operacional/registro_manual.html', {
                'bolsistas': Bolsista.objects.all().order_by('nome'),
                'bolsista_selecionado': bolsista_selecionado,
                'hoje': timezone.now(),
            })
        
        try:
            data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
            try:
                hora_obj = datetime.strptime(horario_str, '%H:%M:%S').time()
            except ValueError:
                hora_obj = datetime.strptime(horario_str, '%H:%M').time()
        except ValueError as e:
            messages.error(request, f'Formato de data/hora inválido: {str(e)}')
            return render(request, 'operacional/registro_manual.html', {
                'bolsistas': Bolsista.objects.all().order_by('nome'),
                'bolsista_selecionado': bolsista_selecionado,
                'hoje': timezone.now(),
            })
        
        freq, created = Frequencia.objects.get_or_create(
            bolsista=bolsista_selecionado,
            data=data_obj,
            defaults={
                'status': 'EM_ABERTO',
                'observacao': observacao
            }
        )
        
        alteracao_texto = ''
        
        if operacao == 'entrada':
            freq.hora_entrada = hora_obj
            if created:
                freq.status = 'EM_ABERTO'
                alteracao_texto = f'Registro manual de entrada: {hora_obj.strftime("%H:%M")}'
            else:
                hora_anterior = freq.hora_entrada
                freq.hora_entrada = hora_obj
                alteracao_texto = f'Ajuste manual de entrada: de {hora_anterior} para {hora_obj.strftime("%H:%M")}'
                
        elif operacao == 'saida':
            freq.hora_saida = hora_obj
            freq.status = 'CONCLUIDA'
            alteracao_texto = f'Registro manual de saída: {hora_obj.strftime("%H:%M")}'
        
        if observacao:
            freq.observacao = observacao
        
        try:
            freq.save()
            
            Historico.objects.create(
                frequencia=freq,
                usuario_responsavel=request.user.username or 'Supervisor',
                alteracao=alteracao_texto + (f'. Obs: {observacao}' if observacao else '')
            )
            
            messages.success(request, f'Ponto registrado com sucesso para {bolsista_selecionado.nome} em {data_obj.strftime("%d/%m/%Y")}.')
            return redirect('frequencia_bolsista', bolsista_id=bolsista_selecionado.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {str(e)}')
            return render(request, 'operacional/registro_manual.html', {
                'bolsistas': Bolsista.objects.all().order_by('nome'),
                'bolsista_selecionado': bolsista_selecionado,
                'hoje': timezone.now(),
            })
    
    context = {
        'bolsistas': Bolsista.objects.all().order_by('nome'),
        'bolsista_selecionado': bolsista_selecionado,
        'hoje': timezone.now(),
    }
    return render(request, 'operacional/registro_manual.html', context)

def comprovantes_mensais(request):
    bolsista_id = 1

    bolsista = get_object_or_404(Bolsista, id=bolsista_id)

    frequencias = (Frequencia.objects.filter(bolsista=bolsista).values('data__year', 'data__month').annotate(ultima_data=Max('data')).order_by('-data__year', '-data__month'))

    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

    comprovantes = []

    for index, registro in enumerate(frequencias, start=1):
        ano = registro['data__year']
        mes = registro['data__month']

        comprovantes.append({
            'id': index,
            'ano': ano,
            'mes': meses[mes - 1],
            'numero_mes': mes,  # Importante: número do mês
            'programa': 'Apoio à Formação Estudantil (PF)',
            'tipo': 'Folha de Frequência',
            'ultima_atualizacao': registro['ultima_data'],
            'arquivo': None,
        })

    context = {
        'comprovantes': comprovantes,
        'bolsista': bolsista,
    }

    return render(request, 'operacional/comprovantes_mensais.html', context)

def relatorio_frequencia(request, ano=None, mes=None):
    bolsista_id = 1  # Temporário: depois vincular ao usuário logado

    bolsista = get_object_or_404(Bolsista, id=bolsista_id)

    hoje = timezone.localtime(timezone.now())

    # Se ano e mês vierem pela URL, usa esses valores.
    # Caso contrário, tenta buscar pelos parâmetros GET.
    if ano is None:
        ano = request.GET.get('ano', hoje.year)

    if mes is None:
        mes = request.GET.get('mes', hoje.month)

    try:
        ano = int(ano)
        mes = int(mes)

        if mes < 1 or mes > 12:
            raise ValueError

    except (ValueError, TypeError):
        ano = hoje.year
        mes = hoje.month

    primeiro_dia = date(ano, mes, 1)

    ultimo_dia = date(
        ano,
        mes,
        calendar.monthrange(ano, mes)[1]
    )

    registros = Frequencia.objects.filter(
        bolsista=bolsista,
        data__range=(primeiro_dia, ultimo_dia)
    ).order_by('data')

    token = gerar_token_qr()
    qr_base64 = gerar_imagem_qr(token)

    context = {
        'registros': registros,
        'bolsista': bolsista,

        'mes': mes,
        'ano': ano,

        'supervisor': None,
        'data_assinatura': hoje,
        'data_emissao': hoje,

        'codigo_verificador': str(bolsista.id).zfill(6),
        'codigo_autenticacao': token,

        'qr_code_url': (
            f"data:image/png;base64,{qr_base64}"
            if qr_base64 else None
        ),
    }

    return render(
        request,
        'operacional/relatorio.html',
        context
    )

