from django.db.models import ForeignKey, CASCADE, OneToOneField
from django.db.models.enums import TextChoices
from django.db.models.fields import CharField, IntegerField

from apps.models.base import CreatedBaseModel
from apps.models.utils import uz_phone_validator


class Favorite(CreatedBaseModel):
    user = ForeignKey('apps.User', CASCADE, related_name='favorites')
    product = ForeignKey('apps.Product', CASCADE, related_name='favorites')


class Cart(CreatedBaseModel):
    user = OneToOneField('apps.User', CASCADE)


class CartItem(CreatedBaseModel):
    cart = ForeignKey('apps.Cart', CASCADE, related_name='cart_items')
    product = ForeignKey('apps.Product', CASCADE, related_name='cart_items')
    quantity = IntegerField(db_default=1)


class PromoCode(CreatedBaseModel):
    code = CharField(max_length=255, unique=True)
    # TODO qaytamiz


class Order(CreatedBaseModel):
    class PaymentType(TextChoices):
        PAYME = 'payme', 'Payme'
        CLICK = 'click', 'Click'
        UZUM_BANK = 'uzum', 'Uzum Bank'
        OLCHA = 'olcha', 'Olcha'
        AFTER_DELIVERED = 'after_delivered', "Yetkazilgandan keyin"

    class Type(TextChoices):
        FULL_PAID = 'full_paid', "To'liq to'lash"
        PARTIAL_PAID = 'partial_paid', "Bo'lib to'lash"

    user = ForeignKey('apps.User', CASCADE, related_name='orders')
    first_name = CharField(max_length=128)
    phone = CharField(max_length=128, validators=[uz_phone_validator])
    type = CharField(max_length=25, choices=Type.choices, default=Type.FULL_PAID)

    payment_type = CharField(max_length=25, choices=PaymentType.choices)
    comment = CharField(max_length=255, null=True, blank=True)


class OrderItem(CreatedBaseModel):
    order = ForeignKey('apps.Order', CASCADE, related_name='order_items')
    product = ForeignKey('apps.Product', CASCADE, related_name='order_items')
    price = IntegerField()
