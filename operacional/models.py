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
    #supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

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
    #supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome