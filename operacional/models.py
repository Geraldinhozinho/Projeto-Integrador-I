from django.db import models

# Create your models here.
class Bolsista(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.CharField(max_length=10, unique=True)
    cpf = models.CharField(max_length=11, unique=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=15, blank=True, null=True)
    setor = models.CharField(max_length=100)
    bolsa = models.ForeignKey('Bolsa', on_delete=models.CASCADE, related_name='bolsistas')

    class Meta:
        verbose_name = 'Bolsista'
        verbose_name_plural = 'Bolsistas'

    def __str__(self):
        return self.nome

class Bolsa(models.Model):
    nome = models.CharField(max_length=100)
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()
    tipo = models.CharField(max_length=50)
    remuneracao = models.DecimalField(max_digits=10, decimal_places=2)
    carga_horaria_semanal = models.IntegerField()

    class Meta:
        verbose_name = 'Bolsa'
        verbose_name_plural = 'Bolsas'

    def __str__(self):
        return self.nome

class Agenda(models.Model):
    titulo = models.CharField(max_length=100)
    bolsista = models.ForeignKey(Bolsista, on_delete=models.CASCADE, related_name='agendas')
    data = models.DateField()
    descricao = models.TextField()

    class Meta:
        verbose_name = 'Agenda'
        verbose_name_plural = 'Agendas'

    def __str__(self):
        return f"{self.bolsista.nome} - {self.data}"