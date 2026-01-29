from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, TextChoices, Model, OneToOneField, CASCADE
from django.db.models.fields import DateField, BigIntegerField

from apps.models.utils import uz_phone_validator
from apps.models.managers import CustomUserManager


class User(AbstractUser):
    class Type(TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'
        SELLER = 'seller', 'Seller'
        MANAGER = 'manager', 'Manager'

    phone = CharField(max_length=15, validators=[uz_phone_validator], unique=True)
    type = CharField(max_length=25, choices=Type.choices, default=Type.USER)
    birth_date = DateField(null=True, blank=True)

    objects = CustomUserManager()

    username = None
    USERNAME_FIELD = 'phone'


class UserBalance(Model):
    user = OneToOneField('apps.User', CASCADE, related_name='user_balance')
    balance = BigIntegerField(default=0)
