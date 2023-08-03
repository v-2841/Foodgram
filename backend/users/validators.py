import re

from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            ('Имя пользователя не может быть <me>.'),
            params={'value': value},
        )
    if re.search(r'^[\w.@+-]+\Z', value) is None:
        raise ValidationError(
            (f'Не допустимые символы <{value}> в нике.'),
            params={'value': value},
        )
