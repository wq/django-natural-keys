# Django Natural Keys

Enhanced support for [natural keys] in Django and [Django REST Framework].  Extracted from [wq.db] for general use.

*Django Natural Keys* provides a number of useful model methods (e.g. `get_or_create_by_natural_key()`) that speed up working with natural keys in Django.  The module also provides a couple of serializer classes that streamline creating REST API support for models with natural keys.

[![Latest PyPI Release](https://img.shields.io/pypi/v/natural-keys.svg)](https://pypi.org/project/natural-keys/)
[![Release Notes](https://img.shields.io/github/release/wq/django-natural-keys.svg)](https://github.com/wq/django-natural-keys/releases)
[![License](https://img.shields.io/pypi/l/natural-keys.svg)](https://github.com/wq/django-natural-keys/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/wq/django-natural-keys.svg)](https://github.com/wq/django-natural-keys/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/wq/django-natural-keys.svg)](https://github.com/wq/django-natural-keys/network)
[![GitHub Issues](https://img.shields.io/github/issues/wq/django-natural-keys.svg)](https://github.com/wq/django-natural-keys/issues)

[![Tests](https://github.com/wq/django-natural-keys/actions/workflows/test.yml/badge.svg)](https://github.com/wq/django-natural-keys/actions/workflows/test.yml)
[![Python Support](https://img.shields.io/pypi/pyversions/natural-keys.svg)](https://pypi.org/project/natural-keys/)
[![Django Support](https://img.shields.io/pypi/djversions/natural-keys.svg)](https://pypi.org/project/natural-keys/)


## Usage

*Django Natural Keys* is available via PyPI:

```bash
# Recommended: create virtual environment
# python3 -m venv venv
# . venv/bin/activate
pip install natural-keys
```

### Model API

To use [natural keys] in vanilla Django, you need to define a `natural_key()` method on your Model class and a `get_natural_key()` method on the Manager class.  With *Django Natural Keys*, you can instead extend `NaturalKeyModel` and define one of the following:

 * A [`UniqueConstraint`][UniqueConstraint] in `Meta.constraints` (recommended),
 * A tuple in [`Meta.unique_together`][unique_together], or
 * A [model field][unique] (other than `AutoField`) with `unique=True`

The first unique constraint found will be treated as the natural key for the model, and all of the necessary functions for working with natural keys will automatically work.

```python
from natural_keys import NaturalKeyModel

class Event(NaturalKeyModel):
    name = models.CharField(max_length=255)
    date = models.DateField()
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'date'),
                name='event_natural_key',
            )
        ]
        
class Note(models.Model):
    event = models.ForeignKey(Event)
    note = models.TextField()
```
or
```python
from natural_keys import NaturalKeyModel

class Event(NaturalKeyModel):
    name = models.CharField(unique=True)
```

The following methods will then be available on your Model and its Manager:

```python
# Default Django methods
instance = Event.objects.get_by_natural_key('ABC123', date(2016, 1, 1))
instance.natural_key == ('ABC123', date(2016, 1, 1))

# get_or_create + natural keys
instance, is_new = Event.objects.get_or_create_by_natural_key('ABC123', date(2016, 1, 1))

# Like get_or_create_by_natural_key, but discards is_new
# Useful for quick lookup/creation when you don't care whether the object exists already
instance = Event.objects.find('ABC123', date(2016, 1, 1))
note = Note.objects.create(
     event=Event.objects.find('ABC123', date(2016, 1, 1)),
     note="This is a note"
)
instance == note.event

# Inspect natural key fields on a model without instantiating it
Event.get_natural_key_fields() == ('name', 'date')
```

#### Nested Natural Keys
One key feature of *Django Natural Keys* is that it will automatically traverse `ForeignKey`s to related models (which should also be `NaturalKeyModel` classes).  This makes it possible to define complex, arbitrarily nested natural keys with minimal effort.

```python
class Place(NaturalKeyModel):
    name = models.CharField(max_length=255, unique=True)

class Event(NaturalKeyModel):
    place = models.ForeignKey(Place)
    date = models.DateField()
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('place', 'date'),
                name='event_natural_key',
            )
        ]
```

```python
Event.get_natural_key_fields() == ('place__name', 'date')
instance = Event.find('ABC123', date(2016, 1, 1))
instance.place.name == 'ABC123'
```

### REST Framework Support
*Django Natural Keys* provides several integrations with [Django REST Framework], primarily through custom Serializer classes.  In most cases, you will want to use either:
 * `NaturalKeyModelSerializer`, or
 * The `natural_key_slug` pseudo-field (see below)

If you have only a single model with a single char field for its natural key, you probably do not need to use either of these integrations.  In your view, you can just use Django REST Framework's built in `lookup_field` to point directly to your natural key.

#### `NaturalKeyModelSerializer`
`NaturalKeyModelSerializer` facilitates handling complex natural keys in your rest API.  It can be used with a `NaturalKeyModel`, or (more commonly) a model that has a foreign key to a `NaturalKeyModel` but is not a `NaturalKeyModel` itself.  (One concrete example of this is the [vera.Report] model, which has a ForeignKey to [vera.Event], which is a `NaturalKeyModel`).

`NaturalKeyModelSerializer` extends DRF's [ModelSerializer], but uses `NaturalKeySerializer` for each foreign key that points to a `NaturalKeyModel`.  When `update()` or `create()`ing the primary model, the nested `NaturalKeySerializer`s will automatically create instances of referenced models if they do not exist already (via the `find()` method described above).  Note that `NaturalKeyModelSerializer` does not override DRF's default behavior for other fields, whether or not they form part of the primary model's natural key.

`NaturalKeySerializer` can technically be used as a top level serializer, though this is not recommended.  `NaturalKeySerializer` is designed for dealing with nested natural keys and does not support updates or non-natural key fields.  Even when used together with `NaturalKeyModelSerializer`, `NaturalKeySerializer` never updates an existing related model instance.  Instead, it will repoint the foreign key to another (potentially new) instance of the related model.  It may help to think of `NaturalKeySerializer` as a special [RelatedField] class rather than as a `Serializer` per se.


You can use `NaturalKeyModelSerializer` with [Django REST Framework] and/or [wq.db] just like any other serializer:
```python
# Django REST Framework usage example
from rest_framework import viewsets
from rest_framework import routers
from natural_keys import NaturalKeyModelSerializer
from .models import Event, Note

class EventSerializer(NaturalKeyModelSerializer):
    class Meta:
        model = Event
        
class NoteSerializer(NaturalKeyModelSerializer):
    class Meta:
        model = Note

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

router = routers.DefaultRouter()
router.register(r'events', EventViewSet)
router.register(r'notes', NoteViewSet)

# wq.db usage example
from wq.db import rest
from natural_keys import NaturalKeyModelSerializer
from .models import Event, Note

rest.router.register_model(Note, serializer=NaturalKeyModelSerializer)
rest.router.register_model(Event, serializer=NaturalKeyModelSerializer)
```

Once this is set up, you can use your REST API to create and view your `NaturalKeyModel` instances and related data.  To facilitate integration with regular HTML Forms, *Django Natural Keys* is integrated with the [HTML JSON Forms] package, which supports nested keys via an array naming convention, as the examples below demonstrate.

```html
<form action="/events/" method="post">
  <input name="place[name]">
  <input type="date" name="date">
</form>
```
```js
// /events.json
[
    {
        "id": 123,
        "place": {"name": "ABC123"},
        "date": "2016-01-01"
    }
]
```
```html
<form action="/notes/" method="post">
  <input name="event[place][name]">
  <input type="date" name="event[date]">
  <textarea name="note"></textarea>
</form>
```
```js
// /notes.json
[
    {
        "id": 12345,
        "event": {
            "place": {"name": "ABC123"},
            "date": "2016-01-01"
        },
        "note": "This is a note"
    }
]
```

### Natural Key Slugs
As an alternative to using `NaturalKeyModelSerializer` / `NaturalKeySerializer`, you can also use a single slug-like field for lookup and serialization.  `NaturalKeyModel` (and its associated queryset) defines a pseudo-field, `natural_key_slug`, for this purpose.

```python
class Place(NaturalKeyModel):
    name = models.CharField(max_length=255, unique=True)
    
class Room(NaturalKeyModel)
    place = models.ForeignKey(Place, models.ON_DELETE)
    name = models.CharField(max_length=255)
    
    class Meta:
        unique_together = (('place', 'name'),)
```
```python
room = Room.objects.find("ABC123", "MainHall")
assert(room.natural_key_slug == "ABC123-MainHall")
assert(room == Room.objects.get(natural_key_slug="ABC123-MainHall"))
```

You can expose this functionality in your REST API to expose natural keys instead of database-generated ids.  To do this, you will likely want to do the following:

 1. Create a regular serializer with `id = serializers.ReadOnlyField(source='natural_key_slug')`
 2. Set `lookup_field = 'natural_key_slug'` on your `ModelViewSet` (or similar generic class) and update the URL registration accordingly
 3. Ensure foreign keys on any related models are serialized with `serializers.SlugRelatedField(slug_field='natural_key_slug')`

In [wq.db], all three of the above can be achieved by setting the `"lookup"` attribute when registering with the [router]:

```python
# myapp/rest.py
from wq.db import rest
from .models import Room

rest.router.register_model(
    Room,
    fields='__all__',
    lookup='natural_key_slug',
)
```

Note that the `natural_key_slug` may not behave as expected if any of the component values contain the delimiter character (`-` by default).  To mitigate this, you can set `natural_key_separator` on the model class to another character.

[natural keys]: https://docs.djangoproject.com/en/4.2/topics/serialization/#natural-keys
[UniqueConstraint]: https://docs.djangoproject.com/en/4.2/ref/models/constraints/#uniqueconstraint
[unique_together]: https://docs.djangoproject.com/en/4.2/ref/models/options/#unique-together
[unique]: https://docs.djangoproject.com/en/4.2/ref/models/fields/#unique

[wq.db]: https://wq.io/wq.db/
[Django REST Framework]: http://www.django-rest-framework.org/
[vera.Report]:https://github.com/powered-by-wq/vera#report
[vera.Event]: https://github.com/powered-by-wq/vera#event
[ModelSerializer]: https://www.django-rest-framework.org/api-guide/serializers/#modelserializer
[RelatedField]: https://www.django-rest-framework.org/api-guide/relations/
[HTML JSON Forms]: https://github.com/wq/html-json-forms
[router]: https://wq.io/wq.db/router
