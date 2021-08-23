from django.db import models
from natural_keys import NaturalKeyModel


class NaturalKeyParent(NaturalKeyModel):
    code = models.CharField(max_length=10)
    group = models.CharField(max_length=10)

    class Meta:
        unique_together = ['code', 'group']


class NaturalKeyChild(NaturalKeyModel):
    parent = models.ForeignKey(NaturalKeyParent, on_delete=models.CASCADE)
    mode = models.CharField(max_length=10)

    class Meta:
        unique_together = ['parent', 'mode']


class ModelWithNaturalKey(models.Model):
    key = models.ForeignKey(NaturalKeyChild, on_delete=models.CASCADE)
    value = models.CharField(max_length=10)


class ModelWithSingleUniqueField(NaturalKeyModel):
    code = models.CharField(max_length=10, unique=True)


class ModelWithExtraField(NaturalKeyModel):
    code = models.CharField(max_length=10)
    date = models.DateField(max_length=10)
    extra = models.TextField()

    class Meta:
        unique_together = ['code', 'date']


class ModelWithConstraint(NaturalKeyModel):
    code = models.CharField(max_length=10)
    date = models.DateField(max_length=10)

    def __str__(self):
        return f'{self.code} {self.date}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='natural key',
                fields=['code', 'date'],
            ),
        ]
