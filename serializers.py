from wq.db.patterns.base.serializers import AttachedModelSerializer
from rest_framework import serializers
from rest_framework.utils import model_meta
from wq.db.rest import compat as html
from .models import NaturalKeyModel


class NaturalKeyValidator(serializers.UniqueTogetherValidator):
    def set_context(self, serializer):
        self.nested_fields = {
            name: serializer.fields[name]
            for name in self.fields
            if isinstance(serializer.fields[name], NaturalKeySerializer)
        }
        super(NaturalKeyValidator, self).set_context(serializer)

    def filter_queryset(self, attrs, queryset):
        attrs = attrs.copy()
        for field in attrs:
            if field in self.nested_fields:
                assert(isinstance(attrs[field], dict))
                cls = self.nested_fields[field].Meta.model
                result = cls._default_manager.filter(
                    **attrs[field]
                )
                if result.count() == 0:
                    # No existing nested object for these values
                    return queryset.none()
                else:
                    # Existing nested object, use it to validate
                    attrs[field] = result[0].pk

        return super(NaturalKeyValidator, self).filter_queryset(
            attrs, queryset
        )


class NaturalKeySerializer(serializers.ModelSerializer):
    """
    Self-nesting Serializer for NaturalKeyModels
    """
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
    def for_model(cls, model_class, validate_key=True):
        unique_together = model_class._meta.unique_together[0]

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

    def to_internal_value(self, data):
        if html.is_html_input(data):
            data = html.parse_json_form(data)
        result = super(NaturalKeySerializer, self).to_internal_value(data)
        return result

    class Meta:
        depth = 1


class NaturalKeyModelSerializer(AttachedModelSerializer):
    """
    Serializer for models with one or more foreign keys to a NaturalKeyModel
    """
    def build_nested_field(self, field_name, relation_info, nested_depth):
        if issubclass(relation_info.related_model, NaturalKeyModel):
            field_class = NaturalKeySerializer.for_model(
                relation_info.related_model,
            )
            return field_class, {}

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
        info = model_meta.get_field_info(self.Meta.model)
        for key in fields:
            if not key.endswith('_id'):
                continue
            field = key[:-3]
            if field in fields or field not in info.relations:
                continue
            relation_info = info.relations[field]
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
            if isinstance(field, NaturalKeySerializer):
                validated_data[name] = fields[name].create(
                    validated_data[name]
                )
