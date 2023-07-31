# flake8: noqa
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
            measurement_unit='test'
        )
        cls.tag = Tag.objects.create(
            name='test',
            color='#81D8D0',
            slug='test'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.recipe = Recipe.objects.create(
            name='test',
            text='test',
            author=cls.user,
            cooking_time=10,
            image=cls.uploaded,
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

    def test(self):
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
        print(data['results'][0]['image'], self.recipe.image)
