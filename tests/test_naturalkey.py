from django.test import TestCase
from tests.test_app.models import (
    NaturalKeyParent, NaturalKeyChild,
    ModelWithSingleUniqueField, ModelWithExtraField, ModelWithConstraint
)
from django.db.utils import IntegrityError

# Tests for natural key models


class NaturalKeyTestCase(TestCase):
    def test_naturalkey_fields(self):
        # Model APIs
        self.assertEqual(
            NaturalKeyParent.get_natural_key_fields(),
            ['code', 'group']
        )
        self.assertEqual(
            NaturalKeyParent(code='code0', group='group0').natural_key(),
            ['code0', 'group0'],
        )
        self.assertEqual(
            NaturalKeyChild.get_natural_key_fields(),
            ['parent__code', 'parent__group', 'mode']
        )
        self.assertEqual(
            ModelWithSingleUniqueField.get_natural_key_fields(),
            ['code']
        )

    def test_naturalkey_create(self):
        # Manager create
        p1 = NaturalKeyParent.objects.create_by_natural_key(
            "code1", "group1"
        )
        self.assertEqual(p1.code, "code1")
        self.assertEqual(p1.group, "group1")

        # get_or_create with same key retrieve existing item
        p2, is_new = NaturalKeyParent.objects.get_or_create_by_natural_key(
            "code1", "group1"
        )
        self.assertFalse(is_new)
        self.assertEqual(p1.pk, p2.pk)

        # Shortcut version
        p3 = NaturalKeyParent.objects.find("code1", "group1")
        self.assertEqual(p1.pk, p3.pk)

        p4 = ModelWithSingleUniqueField.objects.create_by_natural_key(
            "code4"
        )
        self.assertEqual(p4.code, "code4")

    def test_naturalkey_nested_create(self):
        # Manager create, with nested natural key
        c1 = NaturalKeyChild.objects.create_by_natural_key(
            "code2", "group2", "mode1"
        )
        self.assertEqual(c1.parent.code, "code2")
        self.assertEqual(c1.parent.group, "group2")
        self.assertEqual(c1.mode, "mode1")

        # create with same nested key should not create a new parent
        c2 = NaturalKeyChild.objects.create_by_natural_key(
            "code2", "group2", "mode2"
        )
        self.assertEqual(c1.parent.pk, c2.parent.pk)
        self.assertEqual(c2.mode, "mode2")

    def test_naturalkey_duplicate(self):
        # Manager create, with duplicate
        NaturalKeyParent.objects.create_by_natural_key(
            "code1", "group1"
        )
        # create with same key should fail
        with self.assertRaises(IntegrityError):
            NaturalKeyParent.objects.create_by_natural_key(
                "code1", "group1"
            )

    def test_filter_with_Q(self):
        from django.db.models import Q
        query = Q(code="bizarre")
        self.assertEqual(
            ModelWithSingleUniqueField.objects.filter(query).count(),
            0
        )

    def test_find_with_defaults(self):
        obj = ModelWithExtraField.objects.find(
            'extra1',
            '2019-07-26',
            defaults={'extra': 'Test 123'},
        )
        self.assertEqual(
            obj.extra,
            'Test 123'
        )

    def test_find_with_kwargs(self):
        with self.assertRaises(TypeError) as e:
            ModelWithExtraField.objects.find(
                'extra1',
                date='2019-07-26',
            )
        self.assertEqual(
            str(e.exception),
            "find() got an unexpected keyword argument 'date'"
        )

    def test_find_with_constraint(self):
        obj = ModelWithConstraint.objects.find(
            'constraint1',
            '2021-08-23',
        )
        self.assertEqual(
            str(obj),
            'constraint1 2021-08-23'
        )
