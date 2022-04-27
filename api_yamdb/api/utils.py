from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from api_yamdb.settings import DEFAULT_FROM_EMAIL

from rest_framework.exceptions import ValidationError

RESERVED_NAME = 'me'
RESERVED_NAME_ERROR = 'Имя пользователя "me" использовать нельзя.'

CONFIRMATION_CODE = 'Код подтверждения для завершения регистрации'
MESSAGE_FOR_YOUR_CONFIRMATION_CODE = 'Ваш код для получения JWT токена {}'


def validate_username(username):
    if username == RESERVED_NAME:
        raise ValidationError(RESERVED_NAME_ERROR)
    return username


def send_confirmation_code(user, email):
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        CONFIRMATION_CODE,
        MESSAGE_FOR_YOUR_CONFIRMATION_CODE.format(confirmation_code),
        DEFAULT_FROM_EMAIL,
        (email,),
        fail_silently=False,
    )
