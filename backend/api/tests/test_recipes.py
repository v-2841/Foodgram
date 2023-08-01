# type: ignore
import re
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from recipes.models import (Ingredient, IngredientSpecification,
                            Recipe, Tag, TagRecipe)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='user',
            email='user@user.com',
            first_name='first_name',
            last_name='last_name',
        )
        cls.user.set_password('password1234')
        cls.user.save()
        cls.ingredient_specification = IngredientSpecification.objects.create(
            name='test',
            measurement_unit='test',
        )
        cls.tag = Tag.objects.create(
            name='test',
            color='#81D8D0',
            slug='test',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.recipe = Recipe.objects.create(
            name='test',
            text='test',
            author=cls.user,
            cooking_time=10,
            image=cls.uploaded,
        )
        cls.ingredient = Ingredient.objects.create(
            recipe=cls.recipe,
            specification=cls.ingredient_specification,
            amount=100,
        )
        TagRecipe.objects.create(
            tag=cls.tag,
            recipe=cls.recipe,
        )
        cls.base64image = ("data:image/png;base64,iVBORw0KGgoAAAANSU"
                           + "hEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUA"
                           + "AAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxA"
                           + "GVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAA"
                           + "AABJRU5ErkJggg==")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()
        self.authorized_client = APIClient()
        self.token = Token.objects.create(user=self.user)
        self.authorized_client.credentials(HTTP_AUTHORIZATION='Token '
                                           + self.token.key)

    def test_get_recipes_list(self):
        """Проверка доступа к эндпоинту /api/recipes/ методом GET"""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['count', 'next', 'previous', 'results']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        result_expected_keys = ['id', 'tags', 'author', 'ingredients',
                                'is_favorited', 'is_in_shopping_cart',
                                'name', 'image', 'text', 'cooking_time']
        self.assertListEqual(sorted(data['results'][0].keys()),
                             sorted(result_expected_keys))
        result = data['results'][0]
        tag = result['tags'][0]
        tag_expected_keys = ['id', 'name', 'color', 'slug']
        self.assertListEqual(sorted(tag.keys()), sorted(tag_expected_keys))
        self.assertEqual(tag['id'], self.tag.id)
        self.assertEqual(tag['name'], self.tag.name)
        self.assertEqual(tag['color'], self.tag.color)
        self.assertEqual(tag['slug'], self.tag.slug)
        author = result['author']
        author_expected_keys = ['id', 'email', 'username', 'first_name',
                                'last_name', 'is_subscribed']
        self.assertListEqual(sorted(author.keys()),
                             sorted(author_expected_keys))
        self.assertEqual(author['id'], self.user.id)
        self.assertEqual(author['username'], self.user.username)
        self.assertEqual(author['email'], self.user.email)
        self.assertEqual(author['first_name'], self.user.first_name)
        self.assertEqual(author['last_name'], self.user.last_name)
        self.assertFalse(author['is_subscribed'])
        ingredient = result['ingredients'][0]
        ingredient_expected_keys = ['id', 'name', 'measurement_unit', 'amount']
        self.assertListEqual(sorted(ingredient.keys()),
                             sorted(ingredient_expected_keys))
        self.assertEqual(ingredient['id'], self.ingredient.specification.id)
        self.assertEqual(ingredient['name'],
                         self.ingredient.specification.name)
        self.assertEqual(ingredient['measurement_unit'],
                         self.ingredient.specification.measurement_unit)
        self.assertEqual(ingredient['amount'], self.ingredient.amount)
        self.assertFalse(result['is_favorited'])
        self.assertFalse(result['is_in_shopping_cart'])
        self.assertEqual(result['name'], self.recipe.name)
        self.assertEqual(result['text'], self.recipe.text)
        self.assertEqual(result['cooking_time'], self.recipe.cooking_time)
        self.assertEqual(result['image'],
                         'http://testserver/media/recipes/images/small.gif')

    def test_create_recipe(self):
        """Проверка создания нового рецепта POST методом /api/recipes/"""
        counter = Recipe.objects.all().count()
        recipe_data = {
            'ingredients': [
                {
                    'id': self.ingredient_specification.id,
                    'amount': 100,
                }
            ],
            'tags': [self.tag.id],
            'image': self.base64image,
            'name': 'create_test',
            'text': 'create_test',
            'cooking_time': 50,
        }
        response = self.client.post('/api/recipes/', data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authorized_client.post('/api/recipes/', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.authorized_client.post('/api/recipes/',
                                               data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(counter+1, Recipe.objects.all().count())
        data = response.json()
        expected_keys = ['id', 'tags', 'author', 'ingredients', 'is_favorited',
                         'is_in_shopping_cart', 'name', 'image', 'text',
                         'cooking_time']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        tag = data['tags'][0]
        tag_expected_keys = ['id', 'name', 'color', 'slug']
        self.assertListEqual(sorted(tag.keys()), sorted(tag_expected_keys))
        self.assertEqual(tag['id'], self.tag.id)
        self.assertEqual(tag['name'], self.tag.name)
        self.assertEqual(tag['color'], self.tag.color)
        self.assertEqual(tag['slug'], self.tag.slug)
        author = data['author']
        author_expected_keys = ['id', 'email', 'username', 'first_name',
                                'last_name', 'is_subscribed']
        self.assertListEqual(sorted(author.keys()),
                             sorted(author_expected_keys))
        self.assertEqual(author['id'], self.user.id)
        self.assertEqual(author['username'], self.user.username)
        self.assertEqual(author['email'], self.user.email)
        self.assertEqual(author['first_name'], self.user.first_name)
        self.assertEqual(author['last_name'], self.user.last_name)
        self.assertFalse(author['is_subscribed'])
        ingredient = data['ingredients'][0]
        ingredient_expected_keys = ['id', 'name', 'measurement_unit', 'amount']
        self.assertListEqual(sorted(ingredient.keys()),
                             sorted(ingredient_expected_keys))
        self.assertEqual(ingredient['name'],
                         self.ingredient.specification.name)
        self.assertEqual(ingredient['measurement_unit'],
                         self.ingredient.specification.measurement_unit)
        self.assertEqual(ingredient['amount'], self.ingredient.amount)
        self.assertFalse(data['is_favorited'])
        self.assertFalse(data['is_in_shopping_cart'])
        self.assertEqual(data['name'], 'create_test')
        self.assertEqual(data['text'], 'create_test')
        self.assertEqual(data['cooking_time'], 50)
        image = r'http://testserver/media/recipes/images/image(?:_\w+)?\.png'
        self.assertTrue(re.match(image, data['image']))

    def test_update_recipe(self):
        """Проверка редактирования нового рецепта
        PATCH методом /api/recipes/{id}/"""
        old_tag = Tag.objects.create(
            name='old_tag',
            color='#FFFFFF',
            slug='old_tag',
        )
        old_ingredient_specification = IngredientSpecification.objects.create(
            name='old_specification',
            measurement_unit='old_unit',
        )
        recipe = Recipe.objects.create(
            name='test',
            text='test',
            author=self.user,
            cooking_time=10,
            image=self.uploaded,
        )
        TagRecipe.objects.create(
            tag=old_tag,
            recipe=recipe,
        )
        Ingredient.objects.create(
            recipe=recipe,
            specification=old_ingredient_specification,
            amount=25,
        )
        new_tag = Tag.objects.create(
            name='update_test',
            color='#000000',
            slug='update_test'
        )
        ingredient_specification = IngredientSpecification.objects.create(
            name='update_test',
            measurement_unit='update_test',
        )
        recipe_data = {
            'ingredients': [
                {
                    'id': ingredient_specification.id,
                    'amount': 250,
                }
            ],
            'tags': [new_tag.id],
            'image': self.base64image,
            'name': 'update_test',
            'text': 'update_test',
            'cooking_time': 50,
        }
        non_author = User.objects.create(
            username='update_test',
            email='update_test@update_test.com',
            first_name='update_test',
            last_name='update_test',
        )
        token = Token.objects.create(user=non_author)
        non_author_client = APIClient()
        non_author_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.patch(f'/api/recipes/{recipe.id}/',
                                     data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = non_author_client.patch(f'/api/recipes/{recipe.id}/',
                                           data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.authorized_client.patch(f'/api/recipes/{recipe.id}/',
                                                data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.authorized_client.patch('/api/recipes/update_test/',
                                                data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.authorized_client.patch(f'/api/recipes/{recipe.id}/',
                                                data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['id', 'tags', 'author', 'ingredients', 'is_favorited',
                         'is_in_shopping_cart', 'name', 'image', 'text',
                         'cooking_time']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        tag = data['tags'][0]
        tag_expected_keys = ['id', 'name', 'color', 'slug']
        self.assertListEqual(sorted(tag.keys()), sorted(tag_expected_keys))
        self.assertEqual(tag['id'], new_tag.id)
        self.assertEqual(tag['name'], new_tag.name)
        self.assertEqual(tag['color'], new_tag.color)
        self.assertEqual(tag['slug'], new_tag.slug)
        author = data['author']
        author_expected_keys = ['id', 'email', 'username', 'first_name',
                                'last_name', 'is_subscribed']
        self.assertListEqual(sorted(author.keys()),
                             sorted(author_expected_keys))
        self.assertEqual(author['id'], self.user.id)
        self.assertEqual(author['username'], self.user.username)
        self.assertEqual(author['email'], self.user.email)
        self.assertEqual(author['first_name'], self.user.first_name)
        self.assertEqual(author['last_name'], self.user.last_name)
        self.assertFalse(author['is_subscribed'])
        ingredient = data['ingredients'][0]
        ingredient_expected_keys = ['id', 'name', 'measurement_unit', 'amount']
        self.assertListEqual(sorted(ingredient.keys()),
                             sorted(ingredient_expected_keys))
        self.assertEqual(ingredient['name'], ingredient_specification.name)
        self.assertEqual(ingredient['measurement_unit'],
                         ingredient_specification.measurement_unit)
        self.assertEqual(ingredient['amount'], 250)
        self.assertFalse(data['is_favorited'])
        self.assertFalse(data['is_in_shopping_cart'])
        self.assertEqual(data['name'], 'update_test')
        self.assertEqual(data['text'], 'update_test')
        self.assertEqual(data['cooking_time'], 50)
        image = r'http://testserver/media/recipes/images/image(?:_\w+)?\.png'
        self.assertTrue(re.match(image, data['image']))

    def test_delete_recipe(self):
        """Проверка удаления рецепта DELETE методом /api/recipes/{id}/"""
        tag = Tag.objects.create(
            name='tag',
            color='#FFFFFF',
            slug='tag',
        )
        ingredient_specification = IngredientSpecification.objects.create(
            name='ingredient_specification',
            measurement_unit='test_unit',
        )
        recipe = Recipe.objects.create(
            name='test',
            text='test',
            author=self.user,
            cooking_time=10,
            image=self.uploaded,
        )
        TagRecipe.objects.create(
            tag=tag,
            recipe=recipe,
        )
        Ingredient.objects.create(
            recipe=recipe,
            specification=ingredient_specification,
            amount=25,
        )
        non_author = User.objects.create(
            username='update_test',
            email='update_test@update_test.com',
            first_name='update_test',
            last_name='update_test',
        )
        token = Token.objects.create(user=non_author)
        non_author_client = APIClient()
        non_author_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.delete(f'/api/recipes/{recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = non_author_client.delete(f'/api/recipes/{recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.authorized_client.delete('/api/recipes/update_test/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.authorized_client.delete(f'/api/recipes/{recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
