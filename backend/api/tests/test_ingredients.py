# type: ignore
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from recipes.models import IngredientSpecification


class IngredientsAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ingredient = IngredientSpecification.objects.create(
            name='test',
            measurement_unit='test',
        )

    def setUp(self):
        self.client = APIClient()

    def test_get_ingredients_list(self):
        """Проверка доступа к эндпоинту /api/ingredients/ методом GET"""
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()[0]
        expected_keys = ['id', 'name', 'measurement_unit']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        self.assertEqual(data['id'], self.ingredient.id)
        self.assertEqual(data['name'], self.ingredient.name)
        self.assertEqual(data['measurement_unit'],
                         self.ingredient.measurement_unit)

    def test_ingredients_page(self):
        """Проверка доступа к эндпоинту /api/ingredients/{id}/ методом GET"""
        response = self.client.get('/api/ingredients/test_tag/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(f'/api/ingredients/{self.ingredient.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['id', 'name', 'measurement_unit']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        self.assertEqual(data['id'], self.ingredient.id)
        self.assertEqual(data['name'], self.ingredient.name)
        self.assertEqual(data['measurement_unit'],
                         self.ingredient.measurement_unit)
