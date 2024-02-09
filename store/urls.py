from django.urls import path
from .views import ShopView, CartView, ProductSingleView, CartViewSet, WishlistView, WishlistViewSet
from rest_framework import routers

cart_router = routers.DefaultRouter()
cart_router.register(r'cart', CartViewSet, basename='cart')

wishlist_router = routers.DefaultRouter()
wishlist_router.register(r'wishlist', WishlistViewSet, basename='wishlist')

app_name = 'store'

urlpatterns = [
    path('', ShopView.as_view(), name='shop'),
    path('cart/', CartView.as_view(), name='cart'),
    path('product/<int:id>/', ProductSingleView.as_view(), name='product'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:pk>/destroy/', WishlistViewSet.as_view({'post': 'destroy'}), name='wishlist_destroy'),
    path('wishlist/create/', WishlistViewSet.as_view({'post': 'create'}), name='wishlist_create'),
    path('wishlist/add_to_cart/', CartViewSet.as_view({'post': 'create'}), name='add_to_cart'),
]