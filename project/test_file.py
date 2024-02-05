from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from store.models import Product
from store.serializers import ProductSerializer

class WishlistViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.product = Product.objects.create(name='Test Product', description='Test Description', price=10.99)

    def test_add_product_to_wishlist_authenticated_user(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post('/your-wishlist-endpoint/', {'product': self.product.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Товар успешно добавлен в избранное')

    def test_add_product_to_wishlist_anonymous_user(self):
        client = APIClient()

        response = client.post('/your-wishlist-endpoint/', {'product': self.product.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], 'Требуется аутентификация')
