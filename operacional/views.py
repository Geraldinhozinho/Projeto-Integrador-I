from django.shortcuts import render
from .models import Bolsa, Bolsista, Agenda
# Create your views here.


def Index (request):
    return render(request, 'operacional/index.html')

def bolsistas(request):
    bolsistas = Bolsista.objects.all()
    context = {'bolsistas': bolsistas}
    return render(request, 'operacional/bolsistas.html', context)

def bolsas(request):
    bolsas = Bolsa.objects.all()
    context = {'bolsas': bolsas}
    return render(request, 'operacional/bolsas.html', context)

def agendas(request):
    agendas = Agenda.objects.all()
    context = {'agendas': agendas}
    return render(request, 'operacional/agendas.html', context)