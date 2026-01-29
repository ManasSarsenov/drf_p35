from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.core.cache import cache

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, HiddenField, CurrentUserDefault, IntegerField, SerializerMethodField, \
    FloatField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.models import Region, District, Category, Product, User, Order, Seller, ProductImage, CartItem
from apps.models.utils import uz_phone_validator
from apps.tasks import register_key, send_sms_code, generate_random_password


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
        send_sms_code.enqueue(phone, text)
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


#
#
# class RegisterModelSerializer(ModelSerializer):
#     password = CharField(max_length=255, write_only=True)
#     confirm_password = CharField(max_length=255, write_only=True)
#
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'phone', 'password', 'confirm_password']
#
#     def validate_username(self, value: str):
#         if not value.isalpha():
#             raise ValidationError('Invalid username!')
#         return value
#
#     def validate_phone(self, value: str):
#         if not value.startswith('+') or len(value) != 13:
#             raise ValidationError('Invalid phone!')
#         return value
#
#     def validate(self, data):
#         password = data.get('password')
#         confirm_password = data.pop('confirm_password', None)
#         if password != confirm_password:
#             raise ValidationError('Passwords do not match!')
#         data['password'] = make_password(password)
#         return data

class CategoryModelSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', ]

        read_only_fields = []
        # extra_kwargs = {
        #     'address': {'write_only': True}
        # }


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


class ProductListModelSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'discount', ]


#
#
class ProductCreateModelSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'discount', 'category']


# class ChangePasswordSerializer(Serializer):
#     old_password = CharField(required=True)
#     new_password = CharField(required=True, min_length=6)
#     confirm_password = CharField(required=True, min_length=6)
#
#     def validate_old_password(self, value):
#         user = self.context['request'].user
#         if not user.check_password(value):
#             raise serializers.ValidationError('Eski parol natogri')
#         return value
#
#     def validate(self, attrs):
#         if attrs['new_password'] != attrs['confirm_password']:
#             raise serializers.ValidationError('{"confirm_password":"Parollar mos emas"}')
#         return attrs
#
#     def save(self, **kwargs):
#         user = self.context['request'].user
#         user.set_password(self.validated_data['new_password'])
#         user.save()
#         return user

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


class ProductImageModelSerializer(ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']


class ProductModelSerializer(ModelSerializer):
    images = ProductImageModelSerializer(source='products', many=True, read_only=True)
    seller_name = CharField(source='seller.name', read_only=True)
    discount_price = SerializerMethodField()

    class Meta:
        model = Product
        fields = ['slug', 'images', 'seller_name', 'name', 'price', 'discount_price']

    @extend_schema_field(FloatField)
    def get_discount_price(self, obj):
        return obj.price - (obj.price * obj.discount // 100)


class CartItemModelSerializer(ModelSerializer):
    product = ProductModelSerializer(read_only=True)
    quantity = IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']


class CartItemAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found")
        return value

#
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
