from django.db import models
from django.utils import timezone

class Setor(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Supervisor(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.IntegerField()
    email = models.EmailField()
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name="supervisores")

    def __str__(self):
        return self.nome  
    
class Bolsista(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.IntegerField()
    email = models.EmailField()
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name="bolsistas")
    cpf = models.CharField(max_length=11)

    def __str__(self):
        return self.nome
      
class Bolsa(models.Model):
    titulo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    carga_horaria_semanal = models.IntegerField()
    data_inicio = models.DateField()
    data_fim = models.DateField()
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name="bolsas")
    bolsista = models.ManyToManyField(Bolsista, through="Vinculo_bolsista_bolsa", related_name="bolsistas")
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE, related_name="bolsas")
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.titulo
    
class Programa(Bolsa):
    numero_edital = models.CharField(max_length=50)

    def __str__(self):
        return self.titulo
    
class Projeto(Bolsa):
    titulo_projeto = models.CharField(max_length=100)
    objetivo = models.TextField()
    descricao = models.TextField()
    max_participantes_remunerados = models.IntegerField()
    max_participantes_nao_remunerados = models.IntegerField()

    def __str__(self):
        return self.titulo_projeto
    
class Vinculo_bolsista_bolsa(models.Model):
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE, related_name="vinculos")
    bolsa = models.ForeignKey(Bolsa, on_delete=models.CASCADE, related_name="vinculos")
    remuneracao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.bolsista} - {self.bolsa}"  
      
class Agenda(models.Model):
    titulo = models.CharField(max_length=100)
    data = models.DateField()
    descricao = models.TextField()
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name="agendas")
    supervisor = models.ForeignKey('Supervisor', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.data} - {self.titulo} - {self.bolsista.nome}"

class Justificativa(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('REJEITADA', 'Rejeitada'),
    ]

    data_inicio = models.DateField()
    data_final = models.DateField()
    motivo = models.TextField()
    informacao_complementar = models.TextField(blank=True)
    anexo = models.FileField(upload_to='justificativas/', null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDENTE')
    frequencia = models.ForeignKey('Frequencia', on_delete=models.CASCADE, related_name='justificativa', null=True, blank=True)
    bolsista = models.ForeignKey('Bolsista', on_delete=models.CASCADE, related_name='justificativas')

    def __str__(self):
        return f"{self.data_inicio} - {self.data_final} - {self.motivo}"

    def cadastrar_justificativa(self):
        self.status = 'PENDENTE'
        self.save()

    def validar_justificativa(self, aprovado):
        if aprovado:
            self.status = 'APROVADA'
        else:
            self.status = 'REJEITADA'
        self.save()


class Frequencia(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ABERTO', 'Em Aberto'),
        ('CONCLUIDA', 'Concluída'),
        ('FALTA', 'Falta')
    ]
    OBSERVACAO_CHOICES = [
        ('JUSTIFICADA', 'Justificada'),
        ('FIM_DE_SEMANA', 'Fim de Semana'),
        ('FERIADO', 'Feriado')
        ]

    data = models.DateField()
    hora_entrada = models.TimeField(null=True, blank=True)
    hora_saida = models.TimeField(null=True, blank=True)
    assinatura = models.BooleanField(default=False)
    observacao = models.CharField(max_length=50, choices=OBSERVACAO_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='EM_ABERTO')
    documentos = models.FileField(upload_to='documentos_frequencia/', null=True, blank=True)
    bolsista = models.ForeignKey('Bolsista', on_delete=models.CASCADE, related_name='frequencias')
    token_qr = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        ordering = ['-data']
        unique_together = ['bolsista', 'data'] 

    def __str__(self):
        return f"{self.data} - {self.bolsista.nome}"

    def registrar_frequencia(self, bolsista, token=''):
        agora_local = timezone.localtime(timezone.now())
        hoje = agora_local.date()
        agora = agora_local.time()

        if token and Frequencia.objects.filter(token_qr=token).exists():
            return None, "Este QR Code já foi utilizado."

        freq_hoje = Frequencia.objects.filter(bolsista=bolsista, data=hoje).first()

        if not freq_hoje:
            self.bolsista = bolsista
            self.data = hoje
            self.hora_entrada = agora
            self.status = 'EM_ABERTO'
            if token:  
                self.token_qr = token
            self.save()
            return self, "Entrada registrada com sucesso!"
        
        elif freq_hoje.status == 'PENDENTE':
            freq_hoje.hora_entrada = agora
            freq_hoje.status = 'EM_ABERTO'
            if token: 
                freq_hoje.token_qr = token
            freq_hoje.save()
            return freq_hoje, "Entrada registrada com sucesso!"
        
        elif freq_hoje.status == 'EM_ABERTO':
            freq_hoje.hora_saida = agora
            freq_hoje.status = 'CONCLUIDA'
            if token: 
                freq_hoje.token_qr = token
            freq_hoje.save()
            return freq_hoje, "Saída registrada com sucesso!"
        
        else:
            return freq_hoje, "Você já registrou entrada e saída hoje."
          
    def ajustar_frequencia(self, hora_saida, usuario_responsavel, justificativa):
        """Ajusta a frequência manualmente (supervisor) e registra no histórico"""
        hora_saida_anterior = self.hora_saida

        self.hora_saida = hora_saida
        self.status = 'CONCLUIDA'
        self.save()

        Historico.objects.create(
            frequencia=self,
            usuario_responsavel=usuario_responsavel,
            alteracao=f"Horário de saída ajustado de {hora_saida_anterior} para {hora_saida}. Motivo: {justificativa}"
        )

    def assinar_frequencia(self):
        self.assinatura = True
        self.save()

    def ver_frequencia(self):
        return f"Data: {self.data} | Entrada: {self.hora_entrada} | Saída: {self.hora_saida} | Status: {self.status}"


class Historico(models.Model):
    data_hora = models.DateTimeField(auto_now_add=True)
    alteracao = models.TextField()
    frequencia = models.ForeignKey(Frequencia, on_delete=models.CASCADE, related_name='historico')
    usuario_responsavel = models.CharField(max_length=100)

    class Meta:
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.data_hora} - {self.alteracao}"

    def ver_historico(self):
        return f"Data/Hora: {self.data_hora} | Alteração: {self.alteracao} | Responsável: {self.usuario_responsavel}"