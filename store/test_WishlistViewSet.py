from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from store.views import WishlistViewSet
User = get_user_model()

user = User.objects.get(username='admin_el')
request = APIRequestFactory().post('http://127.0.0.1:8000/wishlist/', {})
request.user = user

view = WishlistViewSet.as_view({'post': 'create'})
response = view(request)

print(response.status_code)
print(response.data)
