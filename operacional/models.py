from django.db import models

# Create your models here.

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
    
