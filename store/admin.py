from django.contrib import admin
from .models import Product, Category, Discount, Cart, Profile

admin.site.register(Cart)
admin.site.register(Profile)


from django.contrib import admin
from .models import Category, Product, Discount

# class ProductInline(admin.StackedInline):
#     model = Product
#     extra = 1

class CategoryAdmin(admin.ModelAdmin):
    # inlines = [ProductInline]
    list_display = ('name', 'display_products')

    def display_products(self, obj):
        products = obj.product_set.all()  # Получаем все продукты, связанные с текущей категорией
        return ', '.join([product.name for product in products])  # Возвращаем список имен продуктов в виде строки

    display_products.short_description = 'Products'  # Опционально: устанавливаем короткое описание для колонки

admin.site.register(Category, CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", 'name', "description", 'category', 'price', "image", "created_time", "updated_time")
    list_filter = ('category',)
    search_fields = ('name',)

admin.site.register(Product, ProductAdmin)

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'product', 'value', 'date_begin', 'date_end')
    list_filter = ('product',)
    search_fields = ('product',)
    def display_name(self, obj):
        return str(obj)

admin.site.register(Discount, DiscountAdmin)