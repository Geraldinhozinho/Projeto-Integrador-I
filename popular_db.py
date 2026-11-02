"""
Script para popular o banco de dados do projeto ponto_frequencia.

Como executar:
    python popular_db.py

Coloque este arquivo na raiz do projeto, no mesmo nível de manage.py.

O script localiza os models pelo nome usando o app registry do Django,
portanto não é necessário informar o nome do aplicativo.
"""

import os
from datetime import date, time, timedelta
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ponto_frequencia.settings")

import django
django.setup()

from django.apps import apps
from django.utils import timezone


def obter_model(nome):
    """Localiza um model pelo nome, independentemente do nome do app."""
    encontrados = [
        model for model in apps.get_models()
        if model.__name__ == nome
    ]

    if not encontrados:
        raise LookupError(
            f"Model '{nome}' não encontrado. Verifique se o aplicativo "
            "que contém os models está em INSTALLED_APPS."
        )

    if len(encontrados) > 1:
        raise LookupError(
            f"Há mais de um model chamado '{nome}'. "
            "Nesse caso, informe explicitamente o app_label no script."
        )

    return encontrados[0]


Setor = obter_model("Setor")
Supervisor = obter_model("Supervisor")
Bolsista = obter_model("Bolsista")
Bolsa = obter_model("Bolsa")
Programa = obter_model("Programa")
Projeto = obter_model("Projeto")
Vinculo = obter_model("Vinculo_bolsista_bolsa")
Agenda = obter_model("Agenda")
Frequencia = obter_model("Frequencia")
Justificativa = obter_model("Justificativa")
Historico = obter_model("Historico")


def popular_banco():
    print("Iniciando a população do banco de dados...")

    # ---------------------------------------------------------
    # SETORES
    # ---------------------------------------------------------
    setor_ti, _ = Setor.objects.get_or_create(nome="Tecnologia da Informação")
    setor_adm, _ = Setor.objects.get_or_create(nome="Administração")
    setor_ensino, _ = Setor.objects.get_or_create(nome="Ensino")

    # ---------------------------------------------------------
    # SUPERVISORES
    # ---------------------------------------------------------
    supervisor1, _ = Supervisor.objects.get_or_create(
        matricula=1001,
        defaults={
            "nome": "Carlos Henrique",
            "email": "carlos.henrique@example.com",
            "setor": setor_ti,
        },
    )

    supervisor2, _ = Supervisor.objects.get_or_create(
        matricula=1002,
        defaults={
            "nome": "Maria Oliveira",
            "email": "maria.oliveira@example.com",
            "setor": setor_adm,
        },
    )

    supervisor3, _ = Supervisor.objects.get_or_create(
        matricula=1003,
        defaults={
            "nome": "João Pedro",
            "email": "joao.pedro@example.com",
            "setor": setor_ensino,
        },
    )

    # ---------------------------------------------------------
    # BOLSISTAS
    # ---------------------------------------------------------
    bolsista1, _ = Bolsista.objects.get_or_create(
        matricula=2001,
        defaults={
            "nome": "Ana Beatriz",
            "email": "ana.beatriz@example.com",
            "setor": setor_ti,
            "cpf": "11111111111",
        },
    )

    bolsista2, _ = Bolsista.objects.get_or_create(
        matricula=2002,
        defaults={
            "nome": "Lucas Gabriel",
            "email": "lucas.gabriel@example.com",
            "setor": setor_ti,
            "cpf": "22222222222",
        },
    )

    bolsista3, _ = Bolsista.objects.get_or_create(
        matricula=2003,
        defaults={
            "nome": "Mariana Costa",
            "email": "mariana.costa@example.com",
            "setor": setor_adm,
            "cpf": "33333333333",
        },
    )

    bolsista4, _ = Bolsista.objects.get_or_create(
        matricula=2004,
        defaults={
            "nome": "Pedro Henrique",
            "email": "pedro.henrique@example.com",
            "setor": setor_ensino,
            "cpf": "44444444444",
        },
    )

    # ---------------------------------------------------------
    # PROGRAMAS
    # Programa herda de Bolsa: os campos da classe-base são
    # preenchidos junto com os campos específicos do Programa.
    # ---------------------------------------------------------
    programa1, _ = Programa.objects.get_or_create(
        titulo="Programa de Apoio à Tecnologia",
        defaults={
            "tipo": "Programa",
            "carga_horaria_semanal": 20,
            "data_inicio": date.today() - timedelta(days=30),
            "data_fim": date.today() + timedelta(days=150),
            "setor": setor_ti,
            "supervisor": supervisor1,
            "ativo": True,
            "numero_edital": "EDITAL-001/2026",
        },
    )

    programa2, _ = Programa.objects.get_or_create(
        titulo="Programa de Apoio Administrativo",
        defaults={
            "tipo": "Programa",
            "carga_horaria_semanal": 20,
            "data_inicio": date.today() - timedelta(days=15),
            "data_fim": date.today() + timedelta(days=165),
            "setor": setor_adm,
            "supervisor": supervisor2,
            "ativo": True,
            "numero_edital": "EDITAL-002/2026",
        },
    )

    # ---------------------------------------------------------
    # PROJETOS
    # ---------------------------------------------------------
    projeto1, _ = Projeto.objects.get_or_create(
        titulo="Projeto de Desenvolvimento Web",
        defaults={
            "tipo": "Projeto",
            "carga_horaria_semanal": 20,
            "data_inicio": date.today() - timedelta(days=20),
            "data_fim": date.today() + timedelta(days=160),
            "setor": setor_ti,
            "supervisor": supervisor1,
            "ativo": True,
            "titulo_projeto": "Desenvolvimento de Sistemas Web",
            "objetivo": "Desenvolver soluções web para apoiar os processos institucionais.",
            "descricao": "Projeto voltado ao desenvolvimento e à manutenção de aplicações web.",
            "max_participantes_remunerados": 5,
            "max_participantes_nao_remunerados": 3,
        },
    )

    projeto2, _ = Projeto.objects.get_or_create(
        titulo="Projeto de Organização Administrativa",
        defaults={
            "tipo": "Projeto",
            "carga_horaria_semanal": 12,
            "data_inicio": date.today() - timedelta(days=10),
            "data_fim": date.today() + timedelta(days=170),
            "setor": setor_adm,
            "supervisor": supervisor2,
            "ativo": True,
            "titulo_projeto": "Organização de Processos Administrativos",
            "objetivo": "Melhorar a organização dos processos administrativos.",
            "descricao": "Projeto de apoio à organização e digitalização de documentos.",
            "max_participantes_remunerados": 2,
            "max_participantes_nao_remunerados": 4,
        },
    )

    # ---------------------------------------------------------
    # VÍNCULOS ENTRE BOLSISTAS E BOLSAS
    # O vínculo guarda a remuneração, pois ela pertence à
    # participação do bolsista naquela bolsa.
    # ---------------------------------------------------------
    vinculos = [
        (bolsista1, programa1, Decimal("800.00")),
        (bolsista2, programa1, None),
        (bolsista3, programa2, Decimal("700.00")),
        (bolsista1, projeto1, None),
        (bolsista2, projeto1, Decimal("850.00")),
        (bolsista4, projeto2, Decimal("600.00")),
    ]

    for bolsista, bolsa, remuneracao in vinculos:
        Vinculo.objects.get_or_create(
            bolsista=bolsista,
            bolsa=bolsa,
            defaults={"remuneracao": remuneracao},
        )

    # ---------------------------------------------------------
    # AGENDA
    # ---------------------------------------------------------
    hoje = timezone.localdate()

    eventos = [
        {
            "titulo": "Reunião de acompanhamento",
            "data": hoje + timedelta(days=2),
            "descricao": "Reunião para acompanhar as atividades dos bolsistas.",
            "bolsista": bolsista1,
            "setor": setor_ti,
            "supervisor": supervisor1,
        },
        {
            "titulo": "Entrega de relatório",
            "data": hoje + timedelta(days=5),
            "descricao": "Prazo para entrega do relatório mensal de atividades.",
            "bolsista": bolsista2,
            "setor": setor_ti,
            "supervisor": supervisor1,
        },
        {
            "titulo": "Revisão de atividades",
            "data": hoje + timedelta(days=7),
            "descricao": "Revisão das atividades realizadas no setor.",
            "bolsista": bolsista3,
            "setor": setor_adm,
            "supervisor": supervisor2,
        },
    ]

    for evento in eventos:
        Agenda.objects.get_or_create(
            titulo=evento["titulo"],
            data=evento["data"],
            bolsista=evento["bolsista"],
            defaults={
                "descricao": evento["descricao"],
                "setor": evento["setor"],
                "supervisor": evento["supervisor"],
            },
        )

    # ---------------------------------------------------------
    # FREQUÊNCIAS
    # Cria registros de alguns dias recentes, respeitando a
    # restrição unique_together (bolsista, data).
    # ---------------------------------------------------------
    frequencias_criadas = []

    for bolsista in [bolsista1, bolsista2, bolsista3, bolsista4]:
        for dias_atras in range(1, 6):
            data_frequencia = hoje - timedelta(days=dias_atras)

            # Evita criar frequência em sábado ou domingo.
            if data_frequencia.weekday() >= 5:
                continue

            frequencia, _ = Frequencia.objects.get_or_create(
                bolsista=bolsista,
                data=data_frequencia,
                defaults={
                    "hora_entrada": time(8, 0),
                    "hora_saida": time(12, 0),
                    "assinatura": dias_atras % 2 == 0,
                    "observacao": "Registro de frequência de demonstração.",
                    "status": "CONCLUIDA",
                },
            )
            frequencias_criadas.append(frequencia)

    # Cria uma frequência em aberto para demonstrar o registro
    # de entrada sem saída.
    frequencia_aberta, _ = Frequencia.objects.get_or_create(
        bolsista=bolsista1,
        data=hoje,
        defaults={
            "hora_entrada": time(8, 0),
            "hora_saida": None,
            "assinatura": False,
            "observacao": "Entrada registrada; aguardando saída.",
            "status": "EM_ABERTO",
        },
    )

    # ---------------------------------------------------------
    # JUSTIFICATIVA
    # ---------------------------------------------------------
    frequencia_justificada = frequencias_criadas[0] if frequencias_criadas else None

    if frequencia_justificada:
        Justificativa.objects.get_or_create(
            bolsista=frequencia_justificada.bolsista,
            frequencia=frequencia_justificada,
            defaults={
                "data_inicio": frequencia_justificada.data,
                "data_final": frequencia_justificada.data,
                "motivo": "Consulta médica.",
                "informacao_complementar": "Justificativa cadastrada para demonstração.",
                "status": "PENDENTE",
            },
        )

    # ---------------------------------------------------------
    # HISTÓRICO
    # ---------------------------------------------------------
    Historico.objects.get_or_create(
        frequencia=frequencia_aberta,
        alteracao="Registro de frequência criado para demonstração.",
        usuario_responsavel="Sistema",
    )

    print("\nBanco de dados populado com sucesso!")
    print(f"Setores: {Setor.objects.count()}")
    print(f"Supervisores: {Supervisor.objects.count()}")
    print(f"Bolsistas: {Bolsista.objects.count()}")
    print(f"Programas: {Programa.objects.count()}")
    print(f"Projetos: {Projeto.objects.count()}")
    print(f"Vínculos: {Vinculo.objects.count()}")
    print(f"Agendas: {Agenda.objects.count()}")
    print(f"Frequências: {Frequencia.objects.count()}")
    print(f"Justificativas: {Justificativa.objects.count()}")
    print(f"Históricos: {Historico.objects.count()}")


if __name__ == "__main__":
    popular_banco()
