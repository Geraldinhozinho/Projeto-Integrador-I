from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Max
from functools import wraps
import json
import calendar
from datetime import date, datetime, timedelta
from django.contrib import messages
from .models import Bolsa, Bolsista, Agenda, Frequencia, Justificativa, Historico, Supervisor

try:
    from .utils.qrcode_service import gerar_token_qr, validar_token_qr, gerar_imagem_qr
except ImportError:
    def gerar_token_qr(): return "TOKEN_TESTE"
    def validar_token_qr(t): return True
    def gerar_imagem_qr(t): return ""


# ============================================================
# DECORATOR DE PROTEÇÃO
# ============================================================
def login_necessario(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('bolsista_id') and not request.session.get('supervisor_id'):
            return redirect('login_simples')
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================================
# LOGIN / LOGOUT (Públicas)
# ============================================================
def login_simples(request):
    if request.session.get('bolsista_id'):
        return redirect('frequencia')
    if request.session.get('supervisor_id'):
        return redirect('meus_bolsistas')

    if request.method == 'POST':
        matricula = request.POST.get('matricula', '').strip()
        
        if not matricula:
            messages.error(request, 'Por favor, digite sua matrícula.')
            return render(request, 'operacional/login.html')

        try:
            bolsista = Bolsista.objects.get(matricula=matricula)
            request.session['bolsista_id'] = bolsista.id
            request.session['user_type'] = 'bolsista'
            request.session['user_nome'] = bolsista.nome
            return redirect('frequencia')
        except Bolsista.DoesNotExist:
            pass

        try:
            supervisor = Supervisor.objects.get(matricula=matricula)
            request.session['supervisor_id'] = supervisor.id
            request.session['user_type'] = 'supervisor'
            request.session['user_nome'] = supervisor.nome
            return redirect('meus_bolsistas')
        except Supervisor.DoesNotExist:
            pass

        messages.error(request, 'Matrícula não encontrada no sistema.')

    return render(request, 'operacional/login.html')


def logout_simples(request):
    request.session.flush()
    return redirect('login_simples')


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
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


# ============================================================
# VIEWS PÚBLICAS (Index, Bolsistas, Bolsas, Agendas)
# ============================================================
def Index(request):
    return render(request, 'operacional/index.html')

def bolsistas(request):
    return render(request, 'operacional/bolsistas.html', {'bolsistas': Bolsista.objects.all()})

def bolsas(request):
    return render(request, 'operacional/bolsas.html', {'bolsas': Bolsa.objects.all()})

def agendas(request):
    return render(request, 'operacional/agendas.html', {'agendas': Agenda.objects.all()})


# ============================================================
# FREQUÊNCIA DO BOLSISTA (Protegida)
# ============================================================
@login_necessario
def frequencia(request):
    bolsista_id = request.session.get('bolsista_id')
    
    if not bolsista_id:
        return redirect('meus_bolsistas')

    hoje = timezone.localtime(timezone.now())
    primeiro_dia = hoje.replace(day=1, hour=0, minute=0, second=0)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1], hour=23, minute=59, second=59)
    intervalo_mes = [primeiro_dia.date(), ultimo_dia.date()]
    
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
        'assinatura_disponivel': False,
        'ultima_frequencia': ultima_frequencia,
        'resumo': resumo,
        'is_supervisor': False,
    }
    return render(request, 'operacional/frequencia.html', context)


# ============================================================
# FREQUÊNCIA DE BOLSISTA ESPECÍFICO (Supervisor)
# ============================================================
@login_necessario
def frequencia_bolsista_especifico(request, bolsista_id):
    supervisor_id = request.session.get('supervisor_id')
    
    if not supervisor_id:
        return redirect('frequencia')
        
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    
    hoje = timezone.localtime(timezone.now())
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
        'assinatura_disponivel': False,
        'ultima_frequencia': ultima_frequencia,
        'resumo': resumo,
        'bolsista_selecionado': bolsista,
        'is_supervisor': True,
    }
    return render(request, 'operacional/frequencia.html', context)


# ============================================================
# REGISTRAR ENTRADA / SAÍDA (Protegidas)
# ============================================================
@login_necessario
@require_POST
def registrar_entrada(request):
    bolsista_id = request.session.get('bolsista_id')
    if not bolsista_id:
        return redirect('login_simples')
    
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    freq = Frequencia()
    freq.registrar_frequencia(bolsista, token='') 
    return redirect('frequencia')


@login_necessario
@require_POST
def registrar_saida(request):
    bolsista_id = request.session.get('bolsista_id')
    if not bolsista_id:
        return redirect('login_simples')
    
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    freq = Frequencia()
    freq.registrar_frequencia(bolsista, token='')
    return redirect('frequencia')


# ============================================================
# MEUS BOLSISTAS (Supervisor - Protegida)
# ============================================================
@login_necessario
def meus_bolsistas(request):
    supervisor_id = request.session.get('supervisor_id')
    
    if not supervisor_id:
        return redirect('frequencia')
    
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


# ============================================================
# REGISTRO MANUAL (Supervisor - Protegida)
# ============================================================
@login_necessario
def registrar_ponto_manual(request):
    bolsista_id = request.GET.get('bolsista_id')
    bolsista_selecionado = None
    
    if bolsista_id:
        bolsista_selecionado = get_object_or_404(Bolsista, id=bolsista_id)
    
    if request.method == 'POST':
        post_bolsista_id = request.POST.get('bolsista_id')
        data_str = request.POST.get('data')
        horario_str = request.POST.get('horario')
        operacao = request.POST.get('operacao')
        observacao = request.POST.get('observacao', '')
        
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
                usuario_responsavel=request.session.get('user_nome') or 'Supervisor',
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


# ============================================================
# JUSTIFICATIVAS (Protegidas)
# ============================================================
@login_necessario
def criar_justificativa(request, frequencia_pk=None):
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_final = request.POST.get('data_final')
        motivo = request.POST.get('motivo')
        informacao_complementar = request.POST.get('informacao_complementar', '')
        anexo = request.FILES.get('anexo')
        
        bolsista_id = request.session.get('bolsista_id')
        bolsista = get_object_or_404(Bolsista, id=bolsista_id)
        
        from datetime import datetime
        data_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
        try:
            frequencia_vinculada = Frequencia.objects.get(
                bolsista=bolsista,
                data=data_obj
            )
            print(f"Frequência encontrada: ID={frequencia_vinculada.id} | Data={frequencia_vinculada.data}")
        except Frequencia.DoesNotExist:
            frequencia_vinculada = Frequencia.objects.create(
                bolsista=bolsista,
                data=data_obj,
                status='FALTA',
                observacao='JUSTIFICADA' 
            )
            print(f"Frequência criada: ID={frequencia_vinculada.id} | Data={frequencia_vinculada.data}")
        
        supervisor = bolsista.setor.supervisores.first()
        if not supervisor:
            messages.error(request, 'Nenhum supervisor encontrado para o seu setor.')
            return redirect('frequencia')
        
        justificativa = Justificativa.objects.create(
            bolsista=bolsista,
            frequencia=frequencia_vinculada,  
            data_inicio=data_obj, 
            data_final=datetime.strptime(data_final, '%Y-%m-%d').date(),
            motivo=motivo,
            informacao_complementar=informacao_complementar,
            status='PENDENTE'
        )
        
        if anexo:
            justificativa.anexo = anexo
            justificativa.save()
        
        print(f"Justificativa criada: ID={justificativa.id}")
        print(f"Bolsista: {justificativa.bolsista.nome}")
        print(f"Frequência vinculada: {justificativa.frequencia}")
        print(f"Data frequência: {justificativa.frequencia.data if justificativa.frequencia else 'NULL'}")
        
        messages.success(request, 'Justificativa enviada com sucesso para análise.')
        return redirect('frequencia')
    
    frequencia_obj = None
    if frequencia_pk:
        frequencia_obj = get_object_or_404(
            Frequencia, 
            pk=frequencia_pk, 
            bolsista_id=request.session.get('bolsista_id')
        )
    
    context = {
        'frequencia': frequencia_obj,
    }
    return render(request, 'operacional/criar_justificativa.html', context)

@login_necessario
def ver_justificativa(request, frequencia_pk):
    frequencia = get_object_or_404(Frequencia, pk=frequencia_pk)
    justificativa = frequencia.justificativa.first()
    
    if not justificativa:
        return redirect('frequencia')
    
    context = {
        'frequencia': frequencia,
        'justificativa': justificativa,
        'is_supervisor': request.session.get('user_type') == 'supervisor',
    }
    return render(request, 'operacional/ver_justificativa.html', context)

@login_necessario
def lista_justificativas_bolsista(request, bolsista_id):
    supervisor_id = request.session.get('supervisor_id')
    
    if not supervisor_id:
        return redirect('frequencia')
    
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    
    justificativas = Justificativa.objects.filter(
        bolsista=bolsista
    ).select_related('frequencia').order_by('-data_inicio')
    
    context = {
        'bolsista': bolsista,
        'justificativas': justificativas,
        'total_justificativas': justificativas.count(),
        'pendentes': justificativas.filter(status='PENDENTE').count(),
        'aprovadas': justificativas.filter(status='APROVADA').count(),
        'rejeitadas': justificativas.filter(status='REJEITADA').count(),
    }
    
    return render(request, 'operacional/lista_justificativas_bolsista.html', context)

# ============================================================
# QR CODE (Públicas - usadas pelo scanner)
# ============================================================
def monitor_qrcode(request):
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


# ============================================================
# COMPROVANTES E RELATÓRIOS (Protegidas)
# ============================================================
@login_necessario
def comprovantes_mensais(request, bolsista_id=None):

    # Caso 1: bolsista logado
    bolsista_logado_id = request.session.get('bolsista_id')

    if bolsista_logado_id:
        bolsista = get_object_or_404(
            Bolsista,
            id=bolsista_logado_id
        )

    # Caso 2: supervisor logado
    elif request.session.get('supervisor_id'):

        # Supervisor ainda não escolheu um bolsista
        if bolsista_id is None:
            bolsistas = Bolsista.objects.all().order_by('nome')

            return render(
                request,
                'operacional/selecionar_bolsista_comprovantes.html',
                {
                    'bolsistas': bolsistas,
                }
            )

        # Supervisor escolheu um bolsista
        bolsista = get_object_or_404(
            Bolsista,
            id=bolsista_id
        )

    else:
        return redirect('login_simples')

    # Buscar frequências do bolsista selecionado
    frequencias = (
        Frequencia.objects
        .filter(bolsista=bolsista)
        .values('data__year', 'data__month')
        .annotate(ultima_data=Max('data'))
        .order_by('-data__year', '-data__month')
    )

    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril',
        'Maio', 'Junho', 'Julho', 'Agosto',
        'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    comprovantes = []

    for index, registro in enumerate(frequencias, start=1):
        ano = registro['data__year']
        mes = registro['data__month']

        comprovantes.append({
            'id': index,
            'ano': ano,
            'mes': meses[mes - 1],
            'numero_mes': mes,
            'programa': 'Apoio à Formação Estudantil (PF)',
            'tipo': 'Folha de Frequência',
            'ultima_atualizacao': registro['ultima_data'],
            'arquivo': None,
        })

    context = {
        'comprovantes': comprovantes,
        'bolsista': bolsista,
        'supervisor_visualizando': bool(
            request.session.get('supervisor_id')
        ),
    }

    return render(
        request,
        'operacional/comprovantes_mensais.html',
        context
    )


@login_necessario
def relatorio_frequencia(request, bolsista_id, ano, mes):
    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    
    if not bolsista_id:
        return redirect('frequencia')

    bolsista = get_object_or_404(Bolsista, id=bolsista_id)
    hoje = timezone.localtime(timezone.now())

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
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

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
        'qr_code_url': f"data:image/png;base64,{qr_base64}" if qr_base64 else None,
    }

    return render(
        request,
        'operacional/relatorio.html',
        context
    )

def lista_justificativas_supervisor(request):
    """O superusuário vê TODAS as justificativas do sistema."""
    if not request.user.is_staff:
        return redirect('frequencia')
    
    justificativas = Justificativa.objects.select_related(
        'bolsista', 'frequencia', 'supervisor'
    ).all()
    
    status_filtro = request.GET.get('status', 'PENDENTE')
    if status_filtro != 'TODAS':
        justificativas = justificativas.filter(status=status_filtro)
    
    context = {
        'justificativas': justificativas.order_by('-data_inicio'),
        'status_filtro': status_filtro,
    }
    return render(request, 'operacional/lista_justificativas_supervisor.html', context)


@require_POST
def aprovar_rejeitar_justificativa(request, justificativa_pk):
    if not request.user.is_staff:
        return redirect('frequencia')
    
    justificativa = get_object_or_404(Justificativa, pk=justificativa_pk)
    acao = request.POST.get('acao')
    
    if acao == 'aprovar':
        justificativa.validar_justificativa(aprovado=True)
        if justificativa.frequencia:
            justificativa.frequencia.status = 'JUSTIFICADA'
            justificativa.frequencia.save()
        messages.success(request, f'Justificativa de {justificativa.bolsista.nome} aprovada.')
    elif acao == 'rejeitar':
        justificativa.validar_justificativa(aprovado=False)
        messages.warning(request, f'Justificativa de {justificativa.bolsista.nome} rejeitada.')
    
    if justificativa.frequencia:
        return redirect('ver_justificativa', frequencia_pk=justificativa.frequencia.pk)
    return redirect('frequencia')
