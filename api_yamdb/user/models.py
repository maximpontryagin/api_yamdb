from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from user.constants import CHOICES, MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME, USER
from user.utils import max_length_role
from user.validators import validate_username


class User(AbstractUser):
    """Кастомная модель пользователя."""

    username = models.CharField(max_length=MAX_LENGTH_USERNAME,
                                unique=True,
                                verbose_name='Имя пользователя',
                                validators=[
                                    RegexValidator(
                                        regex='^[a-zA-Z0-9@/./+/-/_]*$',
                                        message='Можно использовать только '
                                        'латинские буквы, цифры и символы '
                                        '@/./+/-/_'
                                    ),
                                    validate_username
                                ])
    email = models.EmailField(max_length=MAX_LENGTH_EMAIL, unique=True,
                              verbose_name='Почта')
    bio = models.TextField(blank=True, verbose_name='Биография')
    role = models.CharField(choices=CHOICES,
                            max_length=max_length_role(),
                            default=USER,
                            verbose_name='Роль')
    confirmation_code = models.CharField(verbose_name='Код подтверждения')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ["username"]

    def is_admin(self, request):
        return request.user.role == 'admin'

    def is_moderator(self, request):
        return request.user.role == 'moderator'

    def __str__(self):
        return self.username


class StreamData:
    def create(self, fields, lst_values):
        if len(fields) != len(lst_values):
            return False
        for i, key in enumerate(fields):
            setattr(self, key, lst_values(i))
        return True
