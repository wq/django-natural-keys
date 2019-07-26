from rest_framework.test import APITestCase
from rest_framework import status
from tests.test_app.models import (
    NaturalKeyParent, NaturalKeyChild, ModelWithNaturalKey,
    ModelWithSingleUniqueField
)
from natural_keys import NaturalKeySerializer
from django.db.utils import IntegrityError

# Tests for natural key models


class NaturalKeyTestCase(APITestCase):
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


class NaturalKeyRestTestCase(APITestCase):
    def test_naturalkey_rest_serializer(self):
        # Serializer should include validator
        serializer = NaturalKeySerializer.for_model(NaturalKeyChild)()
        expect = """
             Serializer():
                 parent = Serializer():
                     code = CharField(max_length=10)
                     group = CharField(max_length=10)
                 mode = CharField(max_length=10)
                 class Meta:
                     validators = [<NaturalKeyValidator(queryset=NaturalKeyChild.objects.all(), fields=('parent', 'mode'))>]""".replace("             ", "")[1:]  # noqa
        self.assertEqual(expect, str(serializer))

        fields = serializer.get_fields()
        self.assertTrue(fields['parent'].required)
        self.assertTrue(fields['mode'].required)
        self.assertTrue(fields['parent'].get_fields()['code'].required)

    def test_naturalkey_rest_singleunique(self):
        # Serializer should only have single top-level validator
        serializer = NaturalKeySerializer.for_model(
            ModelWithSingleUniqueField
        )()
        expect = """
             Serializer():
                 code = CharField(max_length=10, validators=[])
                 class Meta:
                     validators = [<NaturalKeyValidator(queryset=ModelWithSingleUniqueField.objects.all(), fields=('code',))>]""".replace("             ", "")[1:]  # noqa
        self.assertEqual(expect, str(serializer))

        fields = serializer.get_fields()
        self.assertTrue(fields['code'].required)

    def test_naturalkey_rest_post(self):
        # Posting a compound natural key should work
        form = {
            'mode': 'mode3a',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['mode'], "mode3a")
        self.assertEqual(response.data['parent']['code'], "code3")
        self.assertEqual(response.data['parent']['group'], "group3")

        # Posting a simple natural key should work
        form = {
            'code': 'code9',
        }
        response = self.client.post('/modelwithsingleuniquefield.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['code'], "code9")

        # Posting same nested natural key should reuse nested object
        form = {
            'mode': 'mode3b',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(
            NaturalKeyChild.objects.get(mode='mode3a').parent.pk,
            NaturalKeyChild.objects.get(mode='mode3b').parent.pk,
        )

    def test_naturalkey_rest_duplicate(self):
        # Posting identical compound natural key should fail
        form = {
            'mode': 'mode3c',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        form = {
            'mode': 'mode3c',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )
        self.assertEqual(
            response.data, {
                'non_field_errors': [
                    'The fields parent, mode must make a unique set.'
                ]
            }
        )

        # Posting identical simple natural key should fail
        form = {
            'code': 'code8',
        }
        response = self.client.post('/modelwithsingleuniquefield.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        form = {
            'code': 'code8',
        }
        response = self.client.post('/modelwithsingleuniquefield.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )
        self.assertEqual(
            response.data, {
                'code': [
                    'model with single unique field '
                    'with this code already exists.'
                ]
            }
        )

    def test_naturalkey_rest_nested_post(self):
        # Posting a regular model with a ref to natural key
        form = {
            'key[mode]': 'mode4',
            'key[parent][code]': "code4",
            'key[parent][group]': "group4",
            'value': 5,
        }
        response = self.client.post('/modelwithnaturalkeys.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['key']['mode'], "mode4")
        self.assertEqual(response.data['key']['parent']['code'], "code4")
        self.assertEqual(response.data['key']['parent']['group'], "group4")

    def test_naturalkey_rest_nested_put(self):
        # Updating a regular model with a ref to natural key
        instance = ModelWithNaturalKey.objects.create(
            key=NaturalKeyChild.objects.find(
                'code5', 'group5', 'mode5'
            ),
            value=7,
        )
        self.assertEqual(instance.key.parent.code, 'code5')

        # Updating with same natural key should reuse it
        form = {
            'key[mode]': 'mode5',
            'key[parent][code]': "code5",
            'key[parent][group]': "group5",
            'value': 8,
        }
        self.assertEqual(
            NaturalKeyChild.objects.count(),
            1
        )

        # Updating with new natural key should create it
        response = self.client.put(
            '/modelwithnaturalkeys/%s.json' % instance.pk, form
        )
        form = {
            'key[mode]': 'mode6',
            'key[parent][code]': "code6",
            'key[parent][group]': "group6",
            'value': 9,
        }
        response = self.client.put(
            '/modelwithnaturalkeys/%s.json' % instance.pk, form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.assertEqual(response.data['key']['mode'], "mode6")
        self.assertEqual(response.data['key']['parent']['code'], "code6")
        self.assertEqual(response.data['key']['parent']['group'], "group6")
        self.assertEqual(
            NaturalKeyChild.objects.count(),
            2
        )

    def test_naturalkey_lookup(self):
        # Support natural_key_slug as lookup_field setting
        NaturalKeyChild.objects.find(
            'code7', 'group7', 'mode7'
        )
        response = self.client.get(
            '/naturalkeylookup/code7-group7-mode7.json',
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.assertEqual(
            response.data['id'], 'code7-group7-mode7'
        )

    def test_naturalkey_lookup_slug(self):
        # Support separator in slug (but only for last part of key)
        NaturalKeyChild.objects.find(
            'code7', 'group7', 'mode7-alt'
        )
        response = self.client.get(
            '/naturalkeylookup/code7-group7-mode7-alt.json',
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.assertEqual(
            response.data['id'], 'code7-group7-mode7-alt'
        )

    def test_invalid_slug_404(self):
        response = self.client.get(
            '/naturalkeylookup/not-valid.json',
        )
        self.assertEqual(
            status.HTTP_404_NOT_FOUND, response.status_code,
        )

    def test_filter_with_Q(self):
        from django.db.models import Q
        query = Q(code="bizarre")
        self.assertEqual(
            ModelWithSingleUniqueField.objects.filter(query).count(),
            0
        )
