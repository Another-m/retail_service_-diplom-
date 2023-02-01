"""retail_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from app import views
from app.views import *
from .swg_docs import urlpatterns as url_docs

r = DefaultRouter()
r.register('product', ProductViewSet)
r.register('product_params', CategoryProductParametersViewSet, basename='api-product_params')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', user_profile, name='profile'),
    path('confirmation/<str:user>/<str:token>', confirm_email, name='confirmation'),
    path('accounts/profile/', profile_redirect, ),
    path('', index, name='index'),
    path('index/', index, name='index'),
    path('products/', products, name='products'),
    path('products/<str:category>', products_cat, name='products_cat'),
    path('products/<str:category>/<str:subcategory>', products_cat_subcat, name='products_cat_subcat'),
    path('product/<int:prod_id>', product, name='product'),
    path('product_supplier/<int:article_number>', product_supplier, name='product_supplier'),
    path('cabinet/', cabinet, name='cabinet'),
    path('my_price/', price_supplier, name='my_price'),
    path('add_my_price/', products_of_supplier, name='add_my_price'),
    path('order/', order, name='order'),
    path('order/<int:order_id>', order_get, name='order'),
    path('clear/<int:order_id>', clear_order, name='clear'),

    path('api/', include(r.urls)),
    path('api/login/', Login.as_view()),
    path('api/reguser/', RegUser.as_view()),
    path('api/profile/', UserProfile.as_view(), name='api-profile'),
    path('api/orders/', Orders.as_view(), name='api-cabinet'),
    path('api/orders/<int:pk>', Orders.as_view(), name='api-cabinet'),
    path('api/basket/', Basket.as_view(), name='api-basket'),
    path('api/basket/<int:pk>', Basket.as_view(), name='api-basket'),
    path('api/loadingprice/', UploadPrice.as_view(), name='api-loadingprice'),
    path('api/category/', CategoryView.as_view(), name='api-category'),
    path('api/products/', SupProducts.as_view(), name='api-supproducts'),
    path('api/products/<int:pk>', SupProducts.as_view(), name='api-supproducts'),
    path('api/cat_params/', CategoryParametersView.as_view(), name='api-cat_params'),
    path('api/cat_params/<int:pk>', CategoryParametersView.as_view(), name='api-cat_params'),
    path('api/sales/', ActivateSalesView.as_view(), name='api-sales'),

]

urlpatterns += url_docs
