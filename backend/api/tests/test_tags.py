from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from recipes.models import Tag


class TagAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tag = Tag.objects.create(
            name='test_name',
            color='#ffff00',
            slug='test_slug'
        )

    def setUp(self):
        self.client = APIClient()

    def test_get_tags_list(self):
        """Проверка доступа к эндпоинту /api/tags/ методом GET"""
        response = self.client.get('/api/tags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()[0]
        expected_keys = ['id', 'name', 'color', 'slug']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))

    def test_tag_page(self):
        """Проверка доступа к эндпоинту /api/tags/{id}/ методом GET"""
        response = self.client.get('/api/tags/test_tag/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(f'/api/tags/{self.tag.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['id', 'name', 'color', 'slug']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
