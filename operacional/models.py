from django.db import models

# Create your models here.

class Bolsista(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.IntegerField()
    email = models.EmailField()
    setor = models.CharField(max_length=100)
    #cpf = models.CharField(max_length=11)

    def __str__(self):
        return self.nome

class Agenda(models.Model):
    titulo = models.CharField(max_length=100)
    data = models.DateField()
    descricao = models.TextField()
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.data} - {self.titulo} - {self.bolsista.nome}"

class Bolsa(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    carga_horaria_semanal = models.IntegerField()
    remuneracao = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

class Relatorio_de_Frequencia(models.Model):
    mes = models.IntegerField()
    ano = models.IntegerField()
    horas_trabalhadas = models.IntegerField()
    observacao = models.IntegerField(blank=True, null=True)
    data_envio = models.DateField()
    aprovado = models.BoleanField(default=False)
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.mes}/{self.ano} - {self.bolsista.nome}"

class Tarefas(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=50)
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

    def __str__(self):
        return self.titulo
    
class Supervisor(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.IntegerField()
    email = models.EmailField()
    setor = models.CharField(max_length=100)

    def __str__(self):
        return self.nome    
    
class Programa(models.Model):
    nome = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    Bolsa = models.ForeignKey(Bolsa, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome
    
class Projeto(models.Model):
    nome = models.CharField(max_length=100)
    setor = models.CharField(max_length=100)
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()
    objetivo = models.TextField()
    descricao = models.TextField()
    status = models.CharField(max_length=50)
    max_participantes_remunerados = models.IntegerField()
    max_participantes_nao_remunerados = models.IntegerField()
    bolsa = models.ForeignKey(Bolsa, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome
