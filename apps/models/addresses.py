from django.db.models import ForeignKey, CASCADE, Model
from django.db.models.fields import CharField, BooleanField

from apps.models.base import CreatedBaseModel


class Region(Model):
    name = CharField(max_length=255)


class District(Model):
    name = CharField(max_length=255)
    region = ForeignKey('apps.Region', CASCADE, related_name='districts')


class Address(CreatedBaseModel):
    district = ForeignKey('apps.District', CASCADE, related_name='addresses')
    region = ForeignKey('apps.Region', CASCADE, related_name='addresses')
    user = ForeignKey('apps.User', CASCADE, related_name='addresses')
    street = CharField(max_length=255)
    house_number = CharField(max_length=128)
    apartment = CharField(max_length=128, blank=True, null=True)
    entrance = CharField(max_length=128, blank=True, null=True)
    floor = CharField(max_length=128, blank=True, null=True)
    is_standard = BooleanField(db_default=False)
