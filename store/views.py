from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models import F, ExpressionWrapper, DecimalField, Case, When
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from rest_framework import viewsets, response
from rest_framework.permissions import IsAuthenticated

from .models import Product, Cart
from .serializers import CartSerializer, ProductSerializer

User = get_user_model()


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        ## Можно записать так, для получения товара (проверка что он уже есть в корзине)
        # cart_items = Cart.objects.filter(user=request.user,
        #                                  product__id=request.data.get('product'))
        # Или можно так, так как мы переопределили метод get_queryset
        cart_items = self.get_queryset().filter(product__id=request.data.get('product'))
        # request API передаёт параметры по названиям полей в БД, поэтому ловим product
        if cart_items:  # Если продукт уже есть в корзине
            cart_item = cart_items[0]
            if request.data.get('quantity'):  # Если в запросе передан параметр quantity,
                # то добавляем значение к значению в БД
                cart_item.quantity += int(request.data.get('quantity'))
            else:  # Иначе просто добавляем значение по умолчению 1
                cart_item.quantity += 1
        else:  # Если продукта ещё нет в корзине
            product = get_object_or_404(Product, id=request.data.get('product'))  # Получаем продукт и
            # проверяем что он вообще существует, если его нет то выйдет ошибка 404
            if request.data.get('quantity'):  # Если передаём точное количество продукта, то передаём его
                cart_item = Cart(user=request.user, product=product, quantity=request.data.get('quantity'))
            else:  # Иначе создаём объект по умолчанию (quantity по умолчанию = 1, так прописали в моделях)
                cart_item = Cart(user=request.user, product=product)
        cart_item.save()  # Сохранили объект в БД
        return response.Response({'message': 'Product added to cart'},
                                 status=201)  # Вернули ответ, что всё прошло успешно

    def update(self, request, *args, **kwargs):
        # Для удобства в kwargs передаётся id строки для изменения в БД, под параметром pk
        cart_item = get_object_or_404(Cart, id=kwargs['pk'])
        if request.data.get('quantity'):
            cart_item.quantity = request.data['quantity']
        if request.data.get('product'):
            product = get_object_or_404(Product, id=request.data['product'])
            cart_item.product = product
        cart_item.save()
        return response.Response({'message': 'Product change to cart'}, status=201)

    def destroy(self, request, *args, **kwargs):
        # В этот раз напишем примерно так как это делает фреймфорк самостоятельно
        cart_item = self.get_queryset().get(id=kwargs['pk'])
        cart_item.delete()
        return response.Response({'message': 'Product delete from cart'}, status=201)


class WishlistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Если пользователь аутентифицирован, возвращаем избранные товары, иначе возвращаем пустой QuerySet
        return self.request.user.get_wishlist.all() if isinstance(self.request.user, User) else Product.objects.none()

    def create(self, request, *args, **kwargs):
        # Проверяем, является ли пользователь аутентифицированным
        if isinstance(request.user, AnonymousUser):
            return response.Response({'message': 'Требуется аутентификация'}, status=401)

        product_id = request.data.get('product')

        if not product_id:
            return response.Response({'message': 'Отсутствует параметр "product"'}, status=400)

        wishlist_items = self.get_queryset().filter(id=product_id)

        if wishlist_items.exists():
            message = 'Товар уже был добавлен в избранное ранее'
        else:
            product = get_object_or_404(Product, id=product_id)
            user = self.request.user
            user.get_wishlist.add(product)
            message = 'Товар успешно добавлен в избранное'

        return response.Response({'message': message})


class ShopView(View):

    def get(self, request):
        # Создание запроса на получения всех действующих не нулевых скидок
        discount_value = Case(When(discount__value__gte=0,
                                   discount__date_begin__lte=timezone.now(),
                                   discount__date_end__gte=timezone.now(),
                                   then=F('discount__value')),
                              default=0,
                              output_field=DecimalField(max_digits=10, decimal_places=2)
                              )
        # Создание запроса на расчёт цены со скидкой
        price_with_discount = ExpressionWrapper(
            F('price') * (100.0 - F('discount_value')) / 100.0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )

        products = Product.objects.annotate(
            discount_value=discount_value,
            # Другой способ через запрос в другую таблицу, однако
            # без фильтрации по времени действия скидки
            # discount_value=Subquery(
            #     Discount.objects.filter(product_id=OuterRef('id')).values(
            #         'value')
            # ),
            price_before=F('price'),
            price_after=price_with_discount
        ).values('id', 'name', 'image', 'price_before', 'price_after',
                 'discount_value')
        return render(request, 'store/shop.html', {"data": products})


class CartView(View):

    def get(self, request):
        return render(request, "store/cart.html")


class WishlistView(View):

    def get(self, request):
        return render(request, "store/wishlist.html")


class ProductSingleView(View):

    def get(self, request, id):
        # data = {1: {'name': 'Bell Pepper',
        #             'description': 'Bell Pepper',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-1.jpg'},
        #         2: {'name': 'Strawberry',
        #             'description': 'Strawberry',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-2.jpg'},
        #         3: {'name': 'Green Beans',
        #             'description': 'Green Beans',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-3.jpg'},
        #         4: {'name': 'Purple Cabbage',
        #             'description': 'Purple Cabbage',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-4.jpg'},
        #         5: {'name': 'Tomatoe',
        #             'description': 'Tomatoe',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-5.jpg'},
        #         6: {'name': 'Brocolli',
        #             'description': 'Brocolli',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-6.jpg'},
        #         7: {'name': 'Carrots',
        #             'description': 'Carrots',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-7.jpg'},
        #         8: {'name': 'Fruit Juice',
        #             'description': 'Fruit Juice',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-8.jpg'},
        #         9: {'name': 'Onion',
        #             'description': 'Onion',
        #             'price': 120.00,
        #             'rating': 5.0,
        #             'url': 'store/images/product-9.jpg'},
        #         10: {'name': 'Apple',
        #              'description': 'Apple',
        #              'price': 120.00,
        #              'rating': 5.0,
        #              'url': 'store/images/product-10.jpg'},
        #         11: {'name': 'Garlic',
        #              'description': 'Garlic',
        #              'price': 120.00,
        #              'rating': 5.0,
        #              'url': 'store/images/product-11.jpg'},
        #         12: {'name': 'Chilli',
        #              'description': 'Chilli',
        #              'price': 120.00,
        #              'rating': 5.0,
        #              'url': 'store/images/product-12.jpg'}
        #         }
        data = Product.objects.get(id=id)
        return render(request,
                      "store/product-single.html",
                      context={'name': data.name,
                               'description': data.description,
                               'price': data.price,
                               'rating': 5.0,
                               'url': data.image.url,
                               })
