from django.db import models
from natural_keys import NaturalKeyModel


class NaturalKeyParent(NaturalKeyModel):
    code = models.CharField(max_length=10)
    group = models.CharField(max_length=10)

    class Meta:
        unique_together = ['code', 'group']


class NaturalKeyChild(NaturalKeyModel):
    parent = models.ForeignKey(NaturalKeyParent)
    mode = models.CharField(max_length=10)

    class Meta:
        unique_together = ['parent', 'mode']


class ModelWithNaturalKey(models.Model):
    key = models.ForeignKey(NaturalKeyChild)
    value = models.CharField(max_length=10)
