from math import prod
from random import randint

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView, \
    GenericAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import LimitOffsetPagination, CursorPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.models import Region, District, Category, User, Seller, Product, CartItem, Cart
#
# from apps.filters import UserFilterSet, OrderFilterSet
# from apps.models import Category, Product, User, Order
# from apps.paginations import CustomPageNumberPagination, CustomCursorPagination
from apps.serializers import RegionModelSerializer, \
    DistrictModelSerializer, \
    CategoryModelSerializer, \
    CustomTokenObtainPairSerializer, \
    UserModelSerializer, \
    SellerModelSerializer, \
    ProductListModelSerializer, \
    ProductCreateModelSerializer, \
    UserChangePasswordModelSerializer, \
    UserProfileUpdateModelSerializer, UserRegisterModelSerializer, CartItemModelSerializer, CartItemAddSerializer
# CategoryModelSerializer, ProductListModelSerializer, UserModelSerializer,

from apps.tasks import send_sms_code, register_sms


@extend_schema(tags=['regions'])
class RegionListAPIView(ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionModelSerializer
    pagination_class = None


@extend_schema(tags=['regions'])
class DistrictListAPIView(ListAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictModelSerializer
    filter_backends = DjangoFilterBackend,
    filterset_fields = 'region_id',
    pagination_class = None


@extend_schema(tags=['users'])
class UserCheckPhoneAPIView(APIView):
    def get(self, request, phone):
        is_exists = User.objects.filter(phone=phone).exists()
        if not is_exists:
            register_sms.enqueue(phone)

        return Response({'data': {'is_exists': is_exists}})


@extend_schema(tags=['users'])
class UserGetMeRetrieveAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = IsAuthenticated,

    def get_object(self):
        return self.request.user


@extend_schema(tags=['users'])
class UserRegisterCreateAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterModelSerializer


@extend_schema(tags=['users'])
class UserProfileUpdateAPIView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileUpdateModelSerializer
    permission_classes = IsAuthenticated,
    http_method_names = ['patch']

    def get_object(self):
        return self.request.user


@extend_schema(tags=['users'])
class UserChangePasswordUpdateAPIView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserChangePasswordModelSerializer
    permission_classes = IsAuthenticated,
    http_method_names = ['patch']

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True})


class CartItemListAPIView(ListAPIView):
    serializer_class = CartItemModelSerializer
    permission_classes = IsAuthenticated,

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related('product',
                                                                                    'product__seller').prefetch_related(
            'product__products')


# class CartItemAddAPIView(APIView):
#     serializer_class = CartItemModelSerializer
#     permission_classes = IsAuthenticated,
#
#     def post(self, request):
#         user = request.user
#         product_id = request.data.get('product_id')
#         if not product_id:
#             return Response({"detail": "Product id is required"})
#
#         try:
#             product = Product.objects.get(id=product_id)
#         except Product.DoesNotExist:
#             return Response({"detail": "Product not found"})
#
#         quantity = request.data.get('quantity', 1)
#
#         try:
#             quantity = int(quantity)
#             if quantity <= 0:
#                 raise ValueError
#         except (TypeError, ValueError):
#             return Response({"detail": "Invalid quantity"})
#
#         cart, created = Cart.objects.get_or_create(user=user)
#
#         cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
#         if not created:
#             cart_item.quantity += quantity
#         else:
#             cart_item.quantity = quantity
#         cart_item.save()
#
#         serializer = CartItemModelSerializer(cart_item)
#         return Response(serializer.data)

class CartItemAddAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemAddSerializer

    def post(self, request):
        serializer = CartItemAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        product = Product.objects.get(id=product_id)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response(CartItemModelSerializer(cart_item).data)


class CartItemUpdateAPIView(UpdateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemModelSerializer
    permission_classes = IsAuthenticated,
    http_method_names = ['patch', 'put']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(cart__user=self.request.user)

class CartItemDeleteAPIView(DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemModelSerializer
    permission_classes = IsAuthenticated,

    def get_queryset(self):
        return super().get_queryset().filter(cart__user=self.request.user)

# class ChangePasswordAPIView(APIView):
#     serializer_class = ChangePasswordSerializer
#     permission_classes = IsAuthenticated,
#
#     def post(self, request):
#         serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({'detail': "Parol muvaffaqiyatli o'zgartirildi "},
#                         status=status.HTTP_200_OK
#                         )


#
# class RegisterAPIView(CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = RegisterModelSerializer
#
#     def perform_create(self, serializer):
#         serializer.save()
#         # send_email # celery


@extend_schema(tags=['products'])
class CategoryListCreateAPIView(ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryModelSerializer
    pagination_class = None
    permission_classes = IsAuthenticatedOrReadOnly,


class SellerCreateAPIView(CreateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerModelSerializer
    permission_classes = IsAuthenticated,


class CustomTokenObtainPairView(TokenObtainPairView):
    pass
    # serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['products'])
class CategoryRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryModelSerializer


@extend_schema(tags=['products'])
class ProductListCreateAPIView(ListCreateAPIView):
    queryset = Product.objects.order_by('id')
    serializer_class = ProductListModelSerializer
    filter_backends = DjangoFilterBackend, OrderingFilter, SearchFilter
    filterset_fields = ['category_id']

    # filterset_class = ProductFilterSet
    # pagination_class = CustomCursorPagination
    # search_fields = ("name", "category__name")
    # ordering_fields = 'price', 'id'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            self.serializer_class = ProductCreateModelSerializer
        return super().get_serializer_class()

# @extend_schema(tags=['products'])
# class ProductRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductListModelSerializer
#
#
#
# @extend_schema(tags=['users'])
# class UserListAPIView(ListAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserModelSerializer
#     # filterset_fields = ['is_superuser', 'is_staff']
#     filterset_class = UserFilterSet
#     pagination_class = CustomPageNumberPagination
#
#
# @extend_schema(tags=['orders'])
# class OrderListAPIView(ListAPIView):
#     queryset = Order.objects.all()
#     serializer_class = OrderModelSerializer
#     # filterset_fields = ['is_superuser', 'is_staff']
#     filterset_class = OrderFilterSet
