
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError



from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError


class Setor(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Bolsa(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Supervisor(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.IntegerField(unique=True)
    email = models.EmailField()
    setor = models.ForeignKey(
        Setor,
        on_delete=models.PROTECT,
        related_name='supervisores'
    )
    ativo = models.BooleanField(default=True)
    is_supervisor_geral = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class Bolsista(models.Model):
    nome = models.CharField(max_length=100)
    matricula = models.IntegerField(unique=True)
    email = models.EmailField()
    cpf = models.CharField(max_length=11, unique=True)
    ativo = models.BooleanField(default=True)

    setor = models.ForeignKey(
        Setor,
        on_delete=models.PROTECT,
        related_name='bolsistas'
    )
    bolsa = models.ForeignKey(
        Bolsa,
        on_delete=models.PROTECT,
        related_name='bolsistas'
    )
    supervisor = models.ForeignKey(
        Supervisor,
        on_delete=models.PROTECT,
        related_name='bolsistas'
    )

    def clean(self):
        super().clean()

        if not self.supervisor_id or not self.setor_id:
            return

        if not self.supervisor.ativo:
            raise ValidationError({
                'supervisor': 'Não é possível vincular um bolsista a um supervisor inativo.'
            })

        if not self.supervisor.is_supervisor_geral:
            if self.supervisor.setor_id != self.setor_id:
                raise ValidationError({
                    'supervisor': 'O supervisor deve pertencer ao mesmo setor do bolsista ou ser Supervisor Geral.'
                })

    def __str__(self):
        return self.nome


class HistoricoSetorBolsista(models.Model):
    bolsista = models.ForeignKey(
        Bolsista,
        on_delete=models.PROTECT,
        related_name='historico_setores'
    )
    setor = models.ForeignKey(
        Setor,
        on_delete=models.PROTECT,
        related_name='historico_bolsistas'
    )
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['bolsista'],
                condition=Q(data_fim__isnull=True),
                name='um_setor_ativo_por_bolsista'
            )
        ]

    def __str__(self):
        return f'{self.bolsista} - {self.setor}'
