from django.db.models import ForeignKey, CASCADE, Model
from django.db.models.fields import CharField

from apps.models.base import SlugBaseModel, CreatedBaseModel, ImageBaseModel


class Seller(SlugBaseModel, CreatedBaseModel):
    name = CharField(max_length=255)
    owner = ForeignKey('apps.User', CASCADE)
    address = CharField(max_length=255)
    type = CharField(max_length=50, choices=[('seller', 'Seller'), ('other', 'Other')], default='seller')


class Manufacturer(CreatedBaseModel, SlugBaseModel, ImageBaseModel):
    name = CharField(max_length=255)

    def __str__(self):
        return self.name


class ManufactureCategory(Model):
    manufacturer = ForeignKey('apps.Manufacturer', CASCADE, to_field='slug')
    category = ForeignKey('apps.Category', CASCADE, to_field='slug')
