from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from app.models import CustomUser, Company, Sales, Category, Product, MainParameters, SupplierProduct, \
    CategoryParameters, ProductParameters, Order, ProductOrder, UserInfo


# class CompanyInline(admin.TabularInline):
#     model = Company.users.through
#     extra = 1

class UserInfoInline(admin.TabularInline):
    model = UserInfo
    extra = 1

@admin.register(CustomUser)
class CustomUser(UserAdmin):
    list_display = ['id', 'username', 'email', 'first_name', 'last_name', 'last_login', 'date_joined', 'is_confirmed', 'is_staff',
                    'is_superuser', ]
    list_display_links = ['username', 'email']
    list_filter = ['first_name', 'last_name', 'last_login', 'date_joined', ]
    list_editable = ['first_name', 'last_name', ]
    inlines = [UserInfoInline]
    # inlines = [CompanyInline]

class SalesInline(admin.TabularInline):
    model = Sales
    extra = 1

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'counterparty_type', 'veb_site', ]
    list_display_links = ['name', 'phone']
    list_filter = ['name', 'counterparty_type']
    list_editable = ['counterparty_type', ]
    inlines = [SalesInline, UserInfoInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'subcategory', ]
    list_display_links = ['category', ]
    list_filter = ['category', ]
    # inlines = [Subcategory]


class MainParametersInline(admin.TabularInline):
    model = MainParameters
    extra = 1

# class CategoryParametersInline(admin.TabularInline):
#     model = CategoryParameters
#     extra = 1

@admin.register(MainParameters)
class MainParametersAdmin(admin.ModelAdmin):
    list_display = ['id', 'product']


class ProductParametersInline(admin.TabularInline):
    model = ProductParameters
    extra = 1


@admin.register(CategoryParameters)
class CategoryParametersAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'subcategory']
    list_display_links = ['id', 'name', ]
    inlines = [ProductParametersInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'article_number', 'subcategory', 'description', ]
    list_display_links = ['name', 'article_number']
    list_filter = ['name', 'subcategory']
    list_editable = ['subcategory', ]
    inlines = [MainParametersInline, ProductParametersInline]


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'company', 'product', 'quantity', 'price', 'price_rrc', 'is_active', ]
    list_display_links = ['company', 'product']
    list_filter = ['company', 'product__name', 'is_active']
    list_editable = ['quantity', 'price', 'price_rrc', 'is_active', ]




class ProductOrderInline(admin.TabularInline):
    model = ProductOrder
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'datetime', ]
    list_display_links = ['user', ]
    list_filter = ['user', 'status']
    list_editable = ['status', ]
    inlines = [ProductOrderInline]
