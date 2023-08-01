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
from users.models import Follow

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
        cls.follower = User.objects.create(
            username='follower',
            email='follower@follower.com',
            first_name='follower',
            last_name='follower',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()
        self.follower_token = Token.objects.create(user=self.follower)
        self.follower_client = APIClient()
        self.follower_client.credentials(HTTP_AUTHORIZATION='Token '
                                         + self.follower_token.key)

    def test_get_subscriptions(self):
        """Проверка доступа к эндпоинту
        /api/users/subscriptions/ методом GET"""
        Follow.objects.create(
            follower=self.follower,
            following=self.user,
        )
        response = self.client.get('/api/users/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.follower_client.get('/api/users/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['count', 'next', 'previous', 'results']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        result = data['results'][0]
        result_expected_keys = ['email', 'id', 'username', 'first_name',
                                'last_name', 'is_subscribed', 'recipes',
                                'recipes_count']
        self.assertListEqual(sorted(result.keys()),
                             sorted(result_expected_keys))
        self.assertEqual(result['id'], self.user.id)
        self.assertEqual(result['username'], self.user.username)
        self.assertEqual(result['email'], self.user.email)
        self.assertEqual(result['first_name'], self.user.first_name)
        self.assertEqual(result['last_name'], self.user.last_name)
        self.assertEqual(result['recipes_count'],
                         Recipe.objects.filter(author=self.user).count())
        self.assertTrue(result['is_subscribed'])
        recipe = result['recipes'][0]
        recipe_expected_keys = ['id', 'name', 'image', 'cooking_time']
        self.assertListEqual(sorted(recipe.keys()),
                             sorted(recipe_expected_keys))
        self.assertEqual(recipe['id'], self.recipe.id)
        self.assertEqual(recipe['name'], self.recipe.name)
        self.assertEqual(recipe['cooking_time'], self.recipe.cooking_time)
        image = r'http://testserver/media/recipes/images/small(?:_\w+)?\.gif'
        self.assertTrue(re.match(image, recipe['image']))
        Follow.objects.filter(
            follower=self.follower,
            following=self.user,
        ).delete()

    def test_post_subscribe(self):
        """Проверка доступа к эндпоинту
        /api/users/{id}/subscribe/ методом POST"""
        response = self.client.post(f'/api/users/{self.user.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.follower_client.post('/api/users/0/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.follower_client.post(
            f'/api/users/{self.user.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        expected_keys = ['email', 'id', 'username', 'first_name',
                         'last_name', 'is_subscribed', 'recipes',
                         'recipes_count']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], self.user.first_name)
        self.assertEqual(data['last_name'], self.user.last_name)
        self.assertEqual(data['recipes_count'],
                         Recipe.objects.filter(author=self.user).count())
        self.assertTrue(data['is_subscribed'])
        recipe = data['recipes'][0]
        recipe_expected_keys = ['id', 'name', 'image', 'cooking_time']
        self.assertListEqual(sorted(recipe.keys()),
                             sorted(recipe_expected_keys))
        self.assertEqual(recipe['id'], self.recipe.id)
        self.assertEqual(recipe['name'], self.recipe.name)
        self.assertEqual(recipe['cooking_time'], self.recipe.cooking_time)
        image = r'http://testserver/media/recipes/images/small(?:_\w+)?\.gif'
        self.assertTrue(re.match(image, recipe['image']))
        response = self.follower_client.post(
            f'/api/users/{self.user.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.follower_client.post(
            f'/api/users/{self.follower.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        Follow.objects.filter(
            follower=self.follower,
            following=self.user,
        ).delete()

    def test_delete_subscribe(self):
        """Проверка доступа к эндпоинту
        /api/users/{id}/subscribe/ методом POST"""
        response = self.follower_client.delete(
            f'/api/users/{self.user.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        follow = Follow.objects.create(
            follower=self.follower,
            following=self.user,
        )
        counter = Follow.objects.count()
        response = self.client.delete(f'/api/users/{self.user.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.follower_client.delete('/api/users/0/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.follower_client.delete(
            f'/api/users/{self.user.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(counter - 1, Follow.objects.count())
        follow.delete()
