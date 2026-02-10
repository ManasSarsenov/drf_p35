from django.contrib.auth.hashers import make_password
from django.db.models import F
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.core.cache import cache

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, HiddenField, CurrentUserDefault, IntegerField, SerializerMethodField, \
    FloatField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.models import Region, District, Category, Product, User, Order, Seller, ProductImage, CartItem, Favorite, \
    Address
from apps.models.utils import uz_phone_validator
from apps.tasks import register_key, send_sms_code, generate_random_password


class DynamicFieldsModelSerializer(ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class RegionModelSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class DistrictModelSerializer(ModelSerializer):
    class Meta:
        model = District
        # fields = '__all__'
        exclude = 'region',


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'phone', 'birth_date', 'email']


class UserProfileUpdateModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'birth_date']


class UserRegisterModelSerializer(ModelSerializer):
    code = IntegerField(min_value=10_000, max_value=999_999, write_only=True)
    phone = CharField(max_length=15, validators=[uz_phone_validator])

    class Meta:
        model = User
        fields = ['phone', 'code']
        extra_kwargs = {
            'phone': {'write_only': True}
        }

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise ValidationError("Phone number already exists")
        return value

    def validate(self, attrs):
        phone = self.initial_data.get('phone')
        code = attrs.pop('code', None)
        cache_code = cache.get(register_key(phone))
        if str(code) != str(cache_code):
            raise ValidationError("Wrong code")
        return attrs

    def create(self, validated_data):
        validated_data.pop('code', None)
        phone = validated_data.get('phone')
        password = generate_random_password()
        validated_data['password'] = make_password(password)
        text = f"Bu sizning parolingiz {password}"
        send_sms_code.delay(phone, text)
        self.user = super().create(validated_data)
        self.user.first_name = f'user-{self.user.id}'
        self.user.save(update_fields=['first_name'])
        return self.user

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        refresh = RefreshToken.for_user(self.user)
        repr["refresh"] = str(refresh)
        repr["access"] = str(refresh.access_token)
        repr["data"] = UserModelSerializer(self.user).data
        return repr


class CategoryModelSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', ]

        read_only_fields = []
        # extra_kwargs = {
        #     'address': {'write_only': True}
        # }


class AddressModelSerializer(ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["user"]


class SellerModelSerializer(ModelSerializer):
    owner = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Seller
        fields = '__all__'


class CustomTokenObtainPairSerializer(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs) -> dict[str, str]:
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data["data"] = UserModelSerializer(self.user).data

        return data


class ProductImageSerializer(ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductImageCreateSerializer(ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['product', 'image']


class ProductListModelSerializer(DynamicFieldsModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'discount', 'category', 'images']


class ProductCreateModelSerializer(ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'discount', 'category', 'images']


class UserChangePasswordModelSerializer(ModelSerializer):
    old_password = CharField(max_length=255)
    confirm_password = CharField(max_length=255)

    class Meta:
        model = User
        fields = ['old_password', 'password', 'confirm_password']

    def validate(self, attrs: dict):

        for i in set(self.Meta.fields):
            if i not in attrs:
                raise ValidationError(f"{i} field is required")

        old_password = attrs.get('old_password')
        confirm_password = attrs.get('confirm_password')
        password = attrs.get('password')
        user = self.context['request'].user
        if not user.check_password(old_password):
            raise ValidationError("Old password is not correct")

        if password != confirm_password:
            raise ValidationError('Passwords do not match')
        attrs['password'] = make_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        validated_data.pop('old_password', None)
        validated_data.pop('confirm_password', None)
        return super().create(validated_data)


class CartItemModelSerializer(ModelSerializer):
    class Meta:
        model = CartItem
        fields = 'id', 'product', 'quantity'
        extra_kwargs = {
            'quantity': {'read_only': True},
            'product': {'write_only': True}
        }

    def create(self, validated_data):
        obj, updated = CartItem.objects.update_or_create(
            defaults={'quantity': F('quantity') + 1},
            create_defaults={'quantity': 1},
            **validated_data
        )
        return obj

        # cart_item, created = self.Meta.model.objects.get_or_create(**validated_data)
        # if created:
        #     return cart_item
        # cart_item.quantity = F('quantity') + 1
        # cart_item.save(update_fields=['quantity'])
        # return cart_item

    def to_representation(self, instance: CartItem):
        repr_ = super().to_representation(instance)
        user = self.context['request'].user

        repr_.update(
            **ProductListModelSerializer(instance.product,
                                         fields=['name', 'slug', 'price', 'discount', 'first_image']).data)
        repr_['seller_name'] = instance.product.seller.name
        repr_['is_favorite'] = Favorite.objects.filter(user=user, product=instance.product).exists()

        # slug, name, price, discount, image, seller_name, quantity
        return repr_


class FavoriteModelSerializer(DynamicFieldsModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Favorite
        fields = 'id', 'user'

    def to_representation(self, instance: Favorite):
        repr_ = super().to_representation(instance)
        repr_.update(
            **ProductListModelSerializer(instance.product,
                                         fields=['name', 'slug', 'price', 'discount', 'first_image']).data)
        cart_item = CartItem.objects.filter(cart__user=instance.user, product=instance.product).only('quantity').first()
        if cart_item:
            repr_['quantity'] = cart_item.quantity
        else:
            repr_['quantity'] = 0

        return repr_

# class UserModelSerializer(ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'first_name', 'last_name', 'username', 'phone']
#
#
# class OrderModelSerializer(ModelSerializer):
#     class Meta:
#         model = Order
#         fields = '__all__'
