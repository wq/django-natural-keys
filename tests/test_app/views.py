from rest_framework import viewsets
from .models import NaturalKeyChild, ModelWithNaturalKey
from natural_keys import NaturalKeySerializer, NaturalKeyModelSerializer


class NaturalKeyChildViewSet(viewsets.ModelViewSet):
    queryset = NaturalKeyChild.objects.all()
    serializer_class = NaturalKeySerializer.for_model(
        NaturalKeyChild
    )


class ModelWithNaturalKeyViewSet(viewsets.ModelViewSet):
    queryset = ModelWithNaturalKey.objects.all()
    serializer_class = NaturalKeyModelSerializer.for_model(
        ModelWithNaturalKey
    )
