from django.db import models
from functools import reduce


class NaturalKeyQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        natural_key_slug = kwargs.pop("natural_key_slug", None)
        if natural_key_slug and type(natural_key_slug) is str:
            slugs = natural_key_slug.split(self.model.natural_key_separator)
            fields = self.model.get_natural_key_fields()
            if len(slugs) > len(fields):
                slugs[len(fields) - 1 :] = [
                    self.model.natural_key_separator.join(
                        slugs[len(fields) - 1 :]
                    )
                ]
            elif len(slugs) < len(fields):
                return self.none()
            kwargs.update(self.natural_key_kwargs(*slugs))

        return super(NaturalKeyQuerySet, self).filter(*args, **kwargs)

    def natural_key_kwargs(self, *args):
        natural_key = self.model.get_natural_key_fields()
        if len(args) != len(natural_key):
            raise TypeError(
                "Wrong number of values, expected %s" % len(natural_key)
            )
        return dict(zip(natural_key, args))


class NaturalKeyModelManager(models.Manager):
    """
    Manager for use with subclasses of NaturalKeyModel.
    """

    def get_queryset(self):
        return NaturalKeyQuerySet(self.model, using=self._db)

    def get_by_natural_key(self, *args):
        """
        Return the object corresponding to the provided natural key.

        (This is a generic implementation of the standard Django function)
        """

        kwargs = self.natural_key_kwargs(*args)

        # Since kwargs already has __ lookups in it, we could just do this:
        # return self.get(**kwargs)

        # But, we should call each related model's get_by_natural_key in case
        # it's been overridden
        for name, rel_to in self.model.get_natural_key_info():
            if not rel_to:
                continue

            # Extract natural key for related object
            nested_key = extract_nested_key(kwargs, rel_to, name)
            if nested_key:
                # Update kwargs with related object
                try:
                    kwargs[name] = rel_to.objects.get_by_natural_key(
                        *nested_key
                    )
                except rel_to.DoesNotExist:
                    # If related object doesn't exist, assume this one doesn't
                    raise self.model.DoesNotExist()
            else:
                kwargs[name] = None

        return self.get(**kwargs)

    def create_by_natural_key(self, *args, defaults=None):
        """
        Create a new object from the provided natural key values.  If the
        natural key contains related objects, recursively get or create them by
        their natural keys.
        """

        kwargs = self.natural_key_kwargs(*args)
        for name, rel_to in self.model.get_natural_key_info():
            if not rel_to:
                continue
            nested_key = extract_nested_key(kwargs, rel_to, name)
            # Automatically create any related objects as needed
            if nested_key:
                (
                    kwargs[name],
                    is_new,
                ) = rel_to.objects.get_or_create_by_natural_key(*nested_key)
            else:
                kwargs[name] = None
        if defaults:
            attrs = defaults
            attrs.update(kwargs)
        else:
            attrs = kwargs
        return self.create(**attrs)

    def get_or_create_by_natural_key(self, *args, defaults=None):
        """
        get_or_create + get_by_natural_key
        """
        try:
            return (
                self.get_by_natural_key(*args),
                False,
            )
        except self.model.DoesNotExist:
            return (
                self.create_by_natural_key(
                    *args,
                    defaults=defaults,
                ),
                True,
            )

    # Shortcut for common use case
    def find(self, *args, defaults=None):
        """
        Shortcut for get_or_create_by_natural_key that discards the "created"
        boolean.
        """
        obj, is_new = self.get_or_create_by_natural_key(
            *args,
            defaults=defaults,
        )
        return obj

    def natural_key_kwargs(self, *args):
        """
        Convert args into kwargs by merging with model's natural key fieldnames
        """
        return self.get_queryset().natural_key_kwargs(*args)

    def resolve_keys(self, keys, auto_create=False):
        """
        Resolve the list of given keys into objects, if possible.
        Returns a mapping and a success indicator.
        """
        resolved = {}
        success = True
        for key in keys:
            if auto_create:
                resolved[key] = self.find(*key)
            else:
                try:
                    resolved[key] = self.get_by_natural_key(*key)
                except self.model.DoesNotExist:
                    success = False
                    resolved[key] = None
        return resolved, success


class NaturalKeyModel(models.Model):
    """
    Abstract class with a generic implementation of natural_key.
    """

    objects = NaturalKeyModelManager()

    @classmethod
    def get_natural_key_info(cls):
        """
        Derive natural key from first unique_together definition, noting which
        fields are related objects vs. regular fields.
        """
        fields = cls.get_natural_key_def()
        info = []
        for name in fields:
            field = cls._meta.get_field(name)
            rel_to = None
            if hasattr(field, "rel"):
                rel_to = field.rel.to if field.rel else None
            elif hasattr(field, "remote_field"):
                if field.remote_field:
                    rel_to = field.remote_field.model
                else:
                    rel_to = None
            info.append((name, rel_to))
        return info

    @classmethod
    def get_natural_key_def(cls):
        if hasattr(cls, "_natural_key"):
            return cls._natural_key

        for constraint in cls._meta.constraints:
            if isinstance(constraint, models.UniqueConstraint):
                return constraint.fields

        if cls._meta.unique_together:
            return cls._meta.unique_together[0]

        unique = [
            f
            for f in cls._meta.fields
            if f.unique
            and f.__class__.__name__ not in ["AutoField", "BigAutoField"]
        ]
        if unique:
            return (unique[0].name,)

        raise Exception("Add a UniqueConstraint to use natural-keys")

    @classmethod
    def get_natural_key_fields(cls):
        """
        Determine actual natural key field list, incorporating the natural keys
        of related objects as needed.
        """
        natural_key = []
        for name, rel_to in cls.get_natural_key_info():
            if not rel_to:
                natural_key.append(name)
            else:
                nested_key = rel_to.get_natural_key_fields()
                natural_key.extend(
                    [name + "__" + nname for nname in nested_key]
                )
        return tuple(natural_key)

    def natural_key(self):
        """
        Return the natural key for this object.

        (This is a generic implementation of the standard Django function)
        """
        return tuple(
            self.get_natural_key_value(field)
            for field in self.get_natural_key_fields()
        )

    def get_natural_key_value(self, field):
        # Recursively extract properties from related objects if needed
        obj = self
        for part in field.split("__"):
            obj = getattr(obj, part)
            if obj is None:
                return None
        return obj

    natural_key_separator = "-"

    @property
    def natural_key_slug(self):
        return self.natural_key_separator.join(
            str(slug) for slug in self.natural_key()
        )

    class Meta:
        abstract = True


def extract_nested_key(key, cls, prefix=""):
    nested_key = cls.get_natural_key_fields()
    local_fields = {field.name: field for field in cls._meta.local_fields}
    values = []
    has_val = False
    if prefix:
        prefix += "__"
    for nname in nested_key:
        val = key.pop(prefix + nname, None)
        if val is None and nname in local_fields:
            if type(local_fields[nname]).__name__ == "DateTimeField":
                date = key.pop(nname + "_date", None)
                time = key.pop(nname + "_time", None)
                if date and time:
                    val = "%s %s" % (date, time)

        if val is not None:
            has_val = True
        values.append(val)
    if has_val:
        return values
    else:
        return None
