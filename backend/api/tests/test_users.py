# type: ignore
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

USER_PASSWORD = 'password1234'
USER_EMAIL = 'user@user.com'
User = get_user_model()


class UserAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='user',
            email=USER_EMAIL,
            first_name='first_name',
            last_name='last_name',
        )
        cls.user.set_password(USER_PASSWORD)
        cls.user.save()

    def setUp(self):
        self.client = APIClient()
        self.authorized_client = APIClient()
        self.token = Token.objects.create(user=self.user)
        self.authorized_client.credentials(HTTP_AUTHORIZATION='Token '
                                           + self.token.key)

    def test_create_user(self):
        """Проверка создания нового пользователя POST методом /api/users/"""
        counter = User.objects.all().count()
        response = self.client.post('/api/users/', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(counter, User.objects.all().count())
        user_data = {
            'username': 'test_user',
            'password': 'test_password',
            'email': 'test@test.com',
            'first_name': 'first_name',
            'last_name': 'last_name',
        }
        response = self.client.post('/api/users/', data=user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(counter + 1, User.objects.all().count(),
                         'Пользователь не создался')
        data = response.json()
        expected_keys = ['id', 'username', 'email', 'first_name', 'last_name']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        self.assertEqual(data['username'], 'test_user')
        self.assertEqual(data['email'], 'test@test.com')
        self.assertEqual(data['first_name'], 'first_name')
        self.assertEqual(data['last_name'], 'last_name')

    def test_get_users_list(self):
        """Проверка доступа к эндпоинту /api/users/ методом GET"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['count', 'next', 'previous', 'results']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        result = data['results'][0]
        result_expected_keys = ['email', 'id', 'username', 'first_name',
                                'last_name', 'is_subscribed']
        self.assertListEqual(sorted(result.keys()),
                             sorted(result_expected_keys))
        self.assertEqual(result['id'], self.user.id)
        self.assertEqual(result['username'], self.user.username)
        self.assertEqual(result['email'], self.user.email)
        self.assertEqual(result['first_name'], self.user.first_name)
        self.assertEqual(result['last_name'], self.user.last_name)
        self.assertFalse(result['is_subscribed'])

    def test_user_page(self):
        """Проверка доступа к эндпоинту /api/users/{id}/ методом GET"""
        response = self.client.get(f'/api/users/{self.user.pk}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authorized_client.get('/api/users/test_num/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.authorized_client.get(f'/api/users/{self.user.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['email', 'id', 'username',
                         'first_name', 'last_name', 'is_subscribed']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], self.user.first_name)
        self.assertEqual(data['last_name'], self.user.last_name)
        self.assertFalse(data['is_subscribed'])

    def test_me_page(self):
        """Проверка доступа к эндпоинту /api/users/me/ методом GET"""
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authorized_client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = ['email', 'id', 'username',
                         'first_name', 'last_name', 'is_subscribed']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], self.user.first_name)
        self.assertEqual(data['last_name'], self.user.last_name)
        self.assertFalse(data['is_subscribed'])

    def test_delete_user(self):
        """Проверка отсутствия доступа к эндпоинту /api/users/{id}/
        методом DELETE"""
        response = self.client.delete(f'/api/users/{self.user.pk}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authorized_client.delete('/api/users/me/')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.authorized_client.delete(f'/api/users/{self.user.pk}/')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_password_change(self):
        """Проверка доступа к эндпоинту /api/users/set_password/
        методом POST"""
        response = self.client.post('/api/users/set_password/', data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(self.user.check_password(USER_PASSWORD))
        response = self.authorized_client.post('/api/users/set_password/',
                                               data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.authorized_client.post(
            '/api/users/set_password/', data={
                'new_password': 'new_password',
                'current_password': USER_PASSWORD
            })
        self.user = User.objects.get(pk=self.user.pk)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(self.user.check_password('new_password'))
        self.user.set_password(USER_PASSWORD)
        self.user.save()
        self.assertTrue(self.user.check_password(USER_PASSWORD))

    def test_token(self):
        """Проверка доступа к эндпоинту /api/auth/token/"""
        counter = Token.objects.all().count()
        user = User.objects.create(
            username='test_user',
            email='test@test.com',
            first_name='first_name',
            last_name='last_name',
        )
        user.set_password('test_password')
        user.save()
        response = self.client.post('/api/auth/token/login/', {
            'email': 'test@test.com',
            'password': 'test_password'
        })
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK or status.HTTP_201_CREATED)
        self.assertEqual(counter + 1, Token.objects.all().count())
        data = response.json()
        expected_keys = ['auth_token']
        self.assertListEqual(sorted(data.keys()), sorted(expected_keys))
        response = self.client.post('/api/auth/token/logout/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION='Token '
                                + data['auth_token'])
        response = self.client.post('/api/auth/token/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(counter, Token.objects.all().count())
