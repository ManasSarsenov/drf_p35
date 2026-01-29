from django.contrib import admin
from django.contrib.admin import StackedInline

from apps.models import Category, Product, ProductImage, Seller
from apps.models.shops import ManufactureCategory, Manufacturer


class ManufactureCategoryStackedInline(StackedInline):
    model = ManufactureCategory
    extra = 1


@admin.register(Category)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    inlines = [ManufactureCategoryStackedInline]


@admin.register(ProductImage)
class ProductImageModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Manufacturer)
class ManufacturerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(Seller)
class SellerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']