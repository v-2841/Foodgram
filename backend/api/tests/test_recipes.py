# flake8: noqa
# type: ignore
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from recipes.models import Ingredient, IngredientSpecification, Recipe, Tag, TagRecipe

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
        author_expected_keys = ['id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed']
        self.assertListEqual(sorted(author.keys()), sorted(author_expected_keys))
        self.assertEqual(author['id'], self.user.id)
        self.assertEqual(author['username'], self.user.username)
        self.assertEqual(author['email'], self.user.email)
        self.assertEqual(author['first_name'], self.user.first_name)
        self.assertEqual(author['last_name'], self.user.last_name)
        self.assertFalse(author['is_subscribed'])
        ingredient = result['ingredients'][0]
        ingredient_expected_keys = ['id', 'name', 'measurement_unit', 'amount']
        self.assertListEqual(sorted(ingredient.keys()), sorted(ingredient_expected_keys))
        self.assertEqual(ingredient['id'], self.ingredient.id)
        self.assertEqual(ingredient['name'], self.ingredient.specification.name)
        self.assertEqual(ingredient['measurement_unit'], self.ingredient.specification.measurement_unit)
        self.assertEqual(ingredient['amount'], self.ingredient.amount)
        self.assertFalse(result['is_favorited'])
        self.assertFalse(result['is_in_shopping_cart'])
        self.assertEqual(result['name'], self.recipe.name)
        self.assertEqual(result['text'], self.recipe.text)
        self.assertEqual(result['cooking_time'], self.recipe.cooking_time)
        self.assertEqual(result['image'], 'http://testserver/media/recipes/images/small.gif')

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
            'image': "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
            'name': 'create_test',
            'text': 'create_test',
            'cooking_time': 30,
        }
        response = self.client.post('/api/recipes/', data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authorized_client.post('/api/recipes/', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.authorized_client.post('/api/recipes/', data=recipe_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(counter+1, Recipe.objects.all().count())
        data = response.json()
        expected_keys = ['id', 'tags', 'author', 'ingredients', 'is_favorited',
                         'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        tag = data['tags'][0]
        tag_expected_keys = ['id', 'name', 'color', 'slug']
        self.assertListEqual(sorted(tag.keys()), sorted(tag_expected_keys))
        self.assertEqual(tag['id'], self.tag.id)
        self.assertEqual(tag['name'], self.tag.name)
        self.assertEqual(tag['color'], self.tag.color)
        self.assertEqual(tag['slug'], self.tag.slug)
        author = data['author']
        author_expected_keys = ['id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed']
        self.assertListEqual(sorted(author.keys()), sorted(author_expected_keys))
        self.assertEqual(author['id'], self.user.id)
        self.assertEqual(author['username'], self.user.username)
        self.assertEqual(author['email'], self.user.email)
        self.assertEqual(author['first_name'], self.user.first_name)
        self.assertEqual(author['last_name'], self.user.last_name)
        self.assertFalse(author['is_subscribed'])
        ingredient = data['ingredients'][0]
        ingredient_expected_keys = ['id', 'name', 'measurement_unit', 'amount']
        self.assertListEqual(sorted(ingredient.keys()), sorted(ingredient_expected_keys))
        self.assertEqual(ingredient['name'], self.ingredient.specification.name)
        self.assertEqual(ingredient['measurement_unit'], self.ingredient.specification.measurement_unit)
        self.assertEqual(ingredient['amount'], self.ingredient.amount)
        self.assertFalse(data['is_favorited'])
        self.assertFalse(data['is_in_shopping_cart'])
        self.assertEqual(data['name'], 'create_test')
        self.assertEqual(data['text'], 'create_test')
        self.assertEqual(data['cooking_time'], 30)
        self.assertEqual(data['image'], 'http://testserver/media/recipes/images/image.png')
