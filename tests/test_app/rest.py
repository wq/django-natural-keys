from wq.db import rest
from natural_keys import NaturalKeySerializer, NaturalKeyModelSerializer
from .models import NaturalKeyChild, ModelWithNaturalKey


rest.router.register_model(
    NaturalKeyChild,
    serializer=NaturalKeySerializer
)
rest.router.register_model(
    ModelWithNaturalKey,
    serializer=NaturalKeyModelSerializer
)
