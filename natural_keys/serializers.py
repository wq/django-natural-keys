from rest_framework import serializers
from rest_framework.utils import model_meta
from rest_framework.validators import UniqueValidator
from html_json_forms.serializers import JSONFormModelSerializer
from .models import NaturalKeyModel
from collections import OrderedDict


class NaturalKeyValidator(serializers.UniqueTogetherValidator):
    def set_context(self, serializer):
        if getattr(self, 'requires_context', None):
            # DRF 3.11+
            pass
        else:
            # DRF 3.10 and older
            self.serializer = serializer
            super(NaturalKeyValidator, self).set_context(serializer)

    def filter_queryset(self, attrs, queryset, serializer=None):
        if not serializer:
            # DRF 3.10 and older
            serializer = self.serializer

        nested_fields = {
            name: serializer.fields[name]
            for name in self.fields
            if isinstance(serializer.fields[name], NaturalKeySerializer)
        }

        attrs = attrs.copy()
        for field in attrs:
            if field in nested_fields:
                assert(isinstance(attrs[field], dict))
                cls = nested_fields[field].Meta.model
                result = cls._default_manager.filter(
                    **attrs[field]
                )
                if result.count() == 0:
                    # No existing nested object for these values
                    return queryset.none()
                else:
                    # Existing nested object, use it to validate
                    attrs[field] = result[0].pk

        if getattr(self, 'requires_context', None):
            # DRF 3.11+
            return super(NaturalKeyValidator, self).filter_queryset(
                attrs, queryset, serializer
            )
        else:
            # DRF 3.10 and older
            return super(NaturalKeyValidator, self).filter_queryset(
                attrs, queryset
            )


class NaturalKeySerializer(JSONFormModelSerializer):
    """
    Self-nesting Serializer for NaturalKeyModels
    """
    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super(
            NaturalKeySerializer, self
        ).build_standard_field(field_name, model_field)

        if 'validators' in field_kwargs:
            field_kwargs['validators'] = [
                validator
                for validator in field_kwargs.get('validators', [])
                if not isinstance(validator, UniqueValidator)
            ]
        return field_class, field_kwargs

    def build_nested_field(self, field_name, relation_info, nested_depth):
        field_class = NaturalKeySerializer.for_model(
            relation_info.related_model,
            validate_key=False,
        )
        field_kwargs = {}
        return field_class, field_kwargs

    def create(self, validated_data):
        model_class = self.Meta.model
        natural_key_fields = model_class.get_natural_key_fields()
        natural_key = []
        for field in natural_key_fields:
            val = validated_data
            for key in field.split('__'):
                val = val[key]
            natural_key.append(val)
        return model_class.objects.find(*natural_key)

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "Updating an existing natural key is not supported."
        )

    @classmethod
    def for_model(cls, model_class, validate_key=True, include_fields=None):
        unique_together = model_class.get_natural_key_def()
        if include_fields and list(include_fields) != list(unique_together):
            raise NotImplementedError(
                "NaturalKeySerializer for '%s' has unique_together = [%s], "
                "but provided include_fields = [%s]"
                % (model_class._meta.model_name, ', '.join(unique_together),
                   ', '.join(include_fields))
            )

        class Serializer(cls):
            class Meta(cls.Meta):
                model = model_class
                fields = unique_together
                if validate_key:
                    validators = [
                        NaturalKeyValidator(
                            queryset=model_class._default_manager,
                            fields=unique_together,
                        )
                    ]
                else:
                    validators = []
        return Serializer

    @classmethod
    def for_depth(cls, model_class):
        return cls

    class Meta:
        depth = 1


class NaturalKeyModelSerializer(JSONFormModelSerializer):
    """
    Serializer for models with one or more foreign keys to a NaturalKeyModel
    """
    def build_nested_field(self, field_name, relation_info, nested_depth):
        if issubclass(relation_info.related_model, NaturalKeyModel):
            field_class = NaturalKeySerializer.for_model(
                relation_info.related_model,
                validate_key=False,
            )
            field_kwargs = {}
            if relation_info.model_field.null:
                field_kwargs['required'] = False
            return field_class, field_kwargs

        return super(NaturalKeyModelSerializer, self).build_nested_field(
            field_name, relation_info, nested_depth
        )

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(
            NaturalKeyModelSerializer, self
        ).build_relational_field(
            field_name, relation_info
        )
        if issubclass(relation_info.related_model, NaturalKeyModel):
            field_kwargs.pop('queryset')
            field_kwargs['read_only'] = True
        return field_class, field_kwargs

    def get_fields(self):
        fields = super(NaturalKeyModelSerializer, self).get_fields()
        fields.update(self.build_natural_key_fields())
        return fields

    def build_natural_key_fields(self):
        info = model_meta.get_field_info(self.Meta.model)
        fields = OrderedDict()
        for field, relation_info in info.relations.items():
            if not issubclass(relation_info.related_model, NaturalKeyModel):
                continue
            field_class, field_kwargs = self.build_nested_field(
                field, relation_info, 1
            )
            fields[field] = field_class(**field_kwargs)
        return fields

    def create(self, validated_data):
        self.convert_natural_keys(
            validated_data
        )
        return super(NaturalKeyModelSerializer, self).create(
            validated_data
        )

    def update(self, instance, validated_data):
        self.convert_natural_keys(
            validated_data
        )
        return super(NaturalKeyModelSerializer, self).update(
            instance, validated_data
        )

    def convert_natural_keys(self, validated_data):
        fields = self.get_fields()
        for name, field in fields.items():
            if name not in validated_data:
                continue
            if isinstance(field, NaturalKeySerializer):
                validated_data[name] = fields[name].create(
                    validated_data[name]
                )

    @classmethod
    def for_model(cls, model_class, include_fields=None):
        # c.f. wq.db.rest.serializers.ModelSerializer
        class Serializer(cls):
            class Meta(cls.Meta):
                model = model_class
                if include_fields:
                    fields = include_fields
        return Serializer

    class Meta:
        pass
