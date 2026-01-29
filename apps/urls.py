from django.urls import path
# from apps.views import CategoryRetrieveUpdateDestroyAPIView, CategoryListCreateAPIView, ProductListCreateAPIView, \
#     ProductRetrieveUpdateDestroyAPIView, UserListAPIView, OrderListAPIView, RegisterAPIView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from apps.views import RegionListAPIView, DistrictListAPIView, CategoryListCreateAPIView, CustomTokenObtainPairView, \
    UserGetMeRetrieveAPIView, SellerCreateAPIView, ProductListCreateAPIView, UserCheckPhoneAPIView, \
    UserRegisterCreateAPIView, UserChangePasswordUpdateAPIView, UserProfileUpdateAPIView, CartItemUpdateAPIView, \
    CartItemListAPIView, CartItemAddAPIView, CategoryRetrieveUpdateDestroyAPIView, CartItemDeleteAPIView

urlpatterns = [
    path('regions/', RegionListAPIView.as_view()),
    path('districts/', DistrictListAPIView.as_view()),
    path('categories/', CategoryListCreateAPIView.as_view()),
    path('sellers/', SellerCreateAPIView.as_view()),
    path('products/', ProductListCreateAPIView.as_view()),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyAPIView.as_view()),
    # path('products/<int:pk>/', ProductRetrieveUpdateDestroyAPIView.as_view()),
    #
    # path('users/', UserListAPIView.as_view()),
    # path('orders/', OrderListAPIView.as_view()),
    #
    # path('users/register/', RegisterAPIView.as_view()),

    path('users/exists/<int:phone>', UserCheckPhoneAPIView.as_view(), name='users_check_phone'),
    path('change-password/', UserChangePasswordUpdateAPIView.as_view(), name='users_change_password'),
    path('users/update/', UserProfileUpdateAPIView.as_view(), name='users_profile_update'),
    path('users/get-me/', UserGetMeRetrieveAPIView.as_view(), name='token_obtain_pair'),

    path('auth/register/', UserRegisterCreateAPIView.as_view(), name='users_register'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/v1/users/cart/', CartItemListAPIView.as_view(), name='cart-item-list'),
    path('api/v1/users/cart/add/', CartItemAddAPIView.as_view(), name='cart-item-add'),
    path('api/v1/users/cart/<int:pk>/update/', CartItemUpdateAPIView.as_view(), name='cart-item-update'),
    path('api/v1/users/cart/<int:pk>/delete/', CartItemDeleteAPIView.as_view(), name='cart-item-delete'),
]
