try:
    from rest_framework import viewsets
    from rest_framework import serializers
except ImportError:
    pass
else:
    from .models import (
        NaturalKeyChild, ModelWithNaturalKey, ModelWithSingleUniqueField
    )
    from natural_keys import (
        NaturalKeySerializer, NaturalKeyModelSerializer
    )

    class NaturalKeyChildViewSet(viewsets.ModelViewSet):
        queryset = NaturalKeyChild.objects.all()
        serializer_class = NaturalKeySerializer.for_model(
            NaturalKeyChild
        )

    class ModelWithNaturalKeyViewSet(viewsets.ModelViewSet):
        queryset = ModelWithNaturalKey.objects.all()
        serializer_class = NaturalKeyModelSerializer.for_model(
            ModelWithNaturalKey,
            include_fields="__all__",
        )

    class ModelWithSingleUniqueFieldViewSet(viewsets.ModelViewSet):
        queryset = ModelWithSingleUniqueField.objects.all()
        serializer_class = NaturalKeyModelSerializer.for_model(
            ModelWithSingleUniqueField,
            include_fields="__all__",
        )

    class LookupSerializer(NaturalKeyModelSerializer):
        id = serializers.ReadOnlyField(source="natural_key_slug")

        class Meta:
            model = NaturalKeyChild
            fields = "__all__"

    class NaturalKeyLookupViewSet(viewsets.ModelViewSet):
        queryset = NaturalKeyChild.objects.all()
        serializer_class = LookupSerializer
        lookup_field = 'natural_key_slug'
