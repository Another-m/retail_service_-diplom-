from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import login as auth_login
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views, logout, login, authenticate
from django.views import generic
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .data import *
from .forms import LoginForm, RegisterForm
from .loading_files import download_yaml
from .permissions import IsSupplier
from .send_message import send_mail
from .serializers import *


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'app/login.html'

    def form_valid(self, form):
        user = form.user_cache
        verify_email = CustomUser.objects.get(username=user).is_confirmed
        if not verify_email:
            return redirect(f'/confirmation/{user}/0')
        else:
            auth_login(self.request, form.get_user())
            return HttpResponseRedirect(self.get_success_url())


class RegisterView(generic.CreateView):
    form_class = RegisterForm
    template_name = 'app/register.html'
    # success_url = reverse_lazy('login')

    def register_user(self):
        form = RegisterForm(self.request.POST)
        if form.is_valid():
            data = form.cleaned_data
            return data

    def form_valid(self, form):
        data = self.register_user()
        user = form.save()
        create_company(data)

        return redirect(f'/confirmation/{user}/0')

def confirm_email(request, user, token):
    no_data = [0, 'none', '0', 'not', 'null', 'non', 'no', ]
    if token.lower() in no_data:
        if user.lower() in no_data:
            return render(request, 'app/confirm.html',
                          {'info': 'Что-то пошло не так'})
        else:
            verify_user_email(user, None)
            return render(request, 'app/confirm.html',
                          {'info': 'На Ваш е-мэйл отправлено письмо для подтверждения адреса эл. почты'})
    else:
        verify_user_email(user, token)
        return render(request, 'app/confirm.html',
                      {'info': 'Регистрация завершена. Адрес эл. посты успешно подтвержден'})

def logout_user(request):
    logout(request)
    return redirect('login')


# Главная страница
def index(request):
    template = 'app/index.html'
    categories = Category.objects.values('category').distinct()
    subcategories = Category.objects.all()
    suppliers = Company.objects.filter(counterparty_type='supplier')
    products = SupplierProduct.objects.all()

    context = dict(title='Главная страница',
                   suppliers=suppliers,
                   products=products,
                   categories=categories,
                   subcategories=subcategories,
                   )
    return render(request, template, context)


def user_profile(request):
    template = 'app/profile.html'
    username = str(request.user)
    if request.method == "GET":
        company_info = request.GET
        if company_info.get('change'):
            update_user(company_info, username)
    user_info = get_user(username)
    if not user_info:
        return redirect('login')
    request.session['type'] = user_info.users.company.counterparty_type
    statuses = Order.objects.filter(user__username=username)
    order_id = [i.id for i in statuses if 'basket' in i.status]
    if order_id:
        request.session['basket'] = order_id[0]
    context = dict(title='Профиль',
                   user_info=user_info,
                   )
    return render(request, template, context)


def products_context(request, *args):
    order_id = 0
    data = request_params(request, order_id)
    filters = get_filters(request, *args)
    products = filter_products(request, *args)
    print(request.GET)
    quantity_lines = int(request.GET.get("pieces", 12))
    if len(products) % quantity_lines > 0:
        quantity_lines_all = len(products) // quantity_lines + 1
    else:
        quantity_lines_all = len(products) // quantity_lines
    current_page = int(request.GET.get("page", 1))
    paginator = Paginator(products, quantity_lines)
    page = paginator.get_page(current_page)
    next_page_url, prev_page_url = None, None
    if current_page < quantity_lines_all:
        next_page_url = f'?pieces={quantity_lines}&page={current_page + 1}' + filters["filter_supp"]
    if current_page > 1:
        prev_page_url = f'?pieces={quantity_lines}&page={current_page - 1}' + filters["filter_supp"]

    context = dict(title='Каталог товаров',
                   products=page,
                   count=data,
                   filters=filters,
                   current_page=current_page,
                   prev_page_url=prev_page_url,
                   next_page_url=next_page_url,
                   count_page=quantity_lines_all,
                   quantity_lines=quantity_lines,
                   )
    return context

def products(request):
    template = 'app/products.html'
    context = products_context(request)
    return render(request, template, context)

def products_cat(request, category):
    template = 'app/products.html'
    context = products_context(request, category)
    context['filters']['filter_cat'] = category
    return render(request, template, context)

def products_cat_subcat(request, category, subcategory):
    template = 'app/products.html'
    context = products_context(request, category, subcategory)
    context['filters']['filter_cat'] = category
    context['filters']['filter_subcat'] = subcategory
    return render(request, template, context)

def product(request, prod_id):
    template = 'app/product.html'
    order_id = 0
    data = request_params(request, order_id)
    product = SupplierProduct.objects.get(pk=prod_id)
    main_params = MainParameters.objects.get(product=product.product.id)
    other_params = ProductParameters.objects.filter(product=product.product.id)
    context = dict(title='Страница товара',
                   product=product,
                   main_params=main_params,
                   other_params=other_params,
                   count=data,
                   )
    return render(request, template, context)


def cabinet(request):
    template = 'app/cabinet.html'
    username = str(request.user)
    orders = dict(orders='', interval='не выбрано')

    if request.method == "GET":
        date = request.GET
        if date.get('date'):
            orders = get_orders(username, date)
        if date.get('change'):
            print(date)

            orders = update_order(date)

    context = dict(title='Личный кабинет',
                   orders=orders['orders'],
                   interval=orders['interval'],
                   status=Order.STATUS,
                   )
    return render(request, template, context)


def products_of_supplier(request):
    template = 'app/add_my_price.html'
    options_to_choose = dict()

    if request.method == 'POST':
        article_number = 0
        if 'article_number' in request.POST:
            article_number = request.POST.get('article_number')
        options_to_choose = add_product(request, article_number)
    else:
        options_to_choose['categories'] = Category.objects.values('category').distinct()

        # print([i['category'] for i in categories])
    context = dict(title='Личный кабинет',
                   options_to_choose=options_to_choose,

                   )
    return render(request, template, context)

def price_supplier(request):
    template = 'app/my_price.html'
    get_products = SupplierProduct.objects.filter(company__users__user__username=str(request.user))
    if get_products:
        company = get_products.first().company

    else:
        company = Company.objects.filter(users__user__username=str(request.user)).first()
    dwnld_link = f'/static/yaml_files/price_{company.id}.yml'
    if request.method == 'POST':
        if 'price' in request.POST:
            download_yaml(company, get_products)
            return redirect(dwnld_link)
        if 'activate_sales' in request.POST:
            if 'activate_ok' in request.POST:
                Sales.objects.update_or_create(company=company, defaults=dict(activate_sales=True))
            else:
                Sales.objects.update_or_create(company=company, defaults=dict(activate_sales=False))
        if 'is_active' in request.POST:
            if 'active_ok' in request.POST:
                get_products.filter(id=request.POST.get('is_active')).update(is_active=True)
            else:
                get_products.filter(id=request.POST.get('is_active')).update(is_active=False)
    if 'choose' in request.GET and 'del' in request.GET:
        get_products.filter(pk=request.GET.get('choose')).delete()
        get_products = SupplierProduct.objects.filter(company__users__user__username=str(request.user))
    try:
        orders_possibility = Sales.objects.get(company=company)
    except:
        orders_possibility = Sales.objects.create(company=company)

    context = dict(title='Личный кабинет',
                   products=get_products.order_by('id'),
                   dwnld_link=dwnld_link,
                   orders_possibility=orders_possibility,
                   )
    return render(request, template, context)


def product_supplier(request, article_number):
    template = 'app/product_supplier.html'
    order_id = 0
    product_info = dict()
    if request.method == 'POST':
        product_info = add_product(request, article_number)
    if request.method == 'GET':
        product_info = get_product(article_number, request)
    data = request_params(request, order_id)
    context = dict(title='Страница товара',
                   product=product_info['products'],
                   main_params=product_info['main_parameters'],
                   other_params=product_info['other_parameters'],
                   category_params=product_info['category_parameters'],
                   is_exist=product_info['is_exist'],
                   count=data,
                   )
    return render(request, template, context)


def order(request):
    order_id = 0
    if 'basket' in request.session:
        order_id = request.session.get('basket')
    return redirect('order', order_id)


def order_get(request, order_id):
    template = 'app/order.html'
    if request.method == "POST":
        if 'change' in request.POST and 'status' in request.POST:
            update_order(request.POST)
            del request.session['basket']
            return redirect('cabinet')

    data = request_params(request, order_id)
    products = get_order(order_id)


    context = dict(title='Корзина',
                   products=products,
                   count=data,

                   )
    return render(request, template, context)


def profile_redirect(request):
    return redirect('profile')


# Очистить заказ
def clear_order(request, order_id):
    deleted = dell_order(request, order_id)
    if deleted:
        del request.session['basket']
    return redirect('order')


class Login(APIView):
    """
    Класс для авторизации пользователей
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required', 'Необходимо отправить в запросе':
                {"username": "либо Ваше имя пользователя", "email": "либо адрес эл. почты", "password": "пароль"}})
        else:
            return Response({'Status': True, "username": str(request.user)})

    # Авторизация методом POST
    def post(self, request):
        user = 0
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
        elif {'username', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['username'], password=request.data['password'])
        print(user)
        if user != 0:
            if user is not None:
                if user.is_active:
                    if user.is_confirmed:
                        token, _ = Token.objects.get_or_create(user=user)
                        return Response({'Status': True, 'Token': token.key})
                    else:
                        verify_user_email(user, None)
                        return Response({'Status': False, 'Message': 'На Ваш е-мэйл отправлено письмо для подтверждения адреса эл. почты'})

            return Response({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class RegUser(APIView):
    """
    Для регистрации покупателей
    """
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {"user_username", "user_email", "company_name",  "company_tin", "company_type", "post", "password"}.issubset(request.data):

            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []

                for item in password_error:
                    error_array.append(item)
                return Response({'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя
                # request.data._mutable = True
                request.data.update({})
                user_serializer = UserInfoSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    verify_user_email(user, None)
                    return Response({'Status': True})
                else:
                    return Response({'Status': False, 'Errors': user_serializer.errors})

        return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class UserProfile(APIView):
    """
    Класс для получения и редактирования данных пользователя
    """
    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        queryset = UserInfo.objects.filter(user__username=request.user).first()
        serializer = UserInfoSerializer(queryset)
        return Response(serializer.data)

    # Редактирование методом PATCH
    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)

        if 'password' in request.data:
            errors = {}
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return Response({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])

        # проверяем данные
        queryset = UserInfo.objects.filter(user__username=request.user).first()
        user_serializer = UserInfoSerializer(queryset, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response({'Status': True})
        else:
            return Response({'Status': False, 'Errors': user_serializer.errors})


class Orders(APIView):
    """
    Класс для получения информации о заказах и их статусов.
    У покупателя и поставщика личный кабинет отображается по своему.
    """
    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        pk = kwargs.get('pk', None)
        if not pk:
            if c_type == 'supplier':
                queryset = ProductOrder.objects.filter(product__company_id=obj.company.id)
                # Добавляем фильтр по дате (в параметрах гет запроса)
                if {'date_from', 'date_to', }.issubset(request.GET):
                    queryset = queryset.filter(order__datetime__range=(request.GET.get('date_from'), request.GET.get('date_to') + " 23:59"))
                serializer = ProductOrderSerializer(queryset, many=True)
            elif c_type == 'buyer':
                queryset = Order.objects.filter(user=obj.user).annotate(total=Sum('productorders__product__price'),
                                                             count=Count('productorders__product__price')).order_by('id')
                # Добавляем фильтр по дате (в параметрах гет запроса)
                if {'date_from', 'date_to', }.issubset(request.GET):
                    queryset = queryset.filter(datetime__range=(request.GET.get('date_from'),
                                                                request.GET.get('date_to') + " 23:59"))
                serializer = OrderSerializer(queryset, many=True)

        else:
            try:
                queryset = ProductOrder.objects.filter(order_id=pk)
            except:
                return Response({'error': 'Object does not exists'})
            if c_type == 'supplier':
                queryset = queryset.filter(product__company=obj.company)
            serializer = ProductOrderSerializer(queryset, many=True)

        return Response(serializer.data)

    # Изменить статус
    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        pk = kwargs.get('pk', None)
        if pk:
            if c_type == 'supplier':
                if {'order_status', }.issubset(request.data):
                    order = Order.objects.get(pk=pk)
                    order.status = request.data.get('order_status')
                    order.save()
                    serializer = OrdersSerializer(order)
                    return Response(serializer.data)
                else:
                    return Response({"error": "Не вверный ввод, в данном запросе возможно изменить только статус",
                                      "пример": "order_status: new"})
            else:
                return Response({"error": "покупатель не может вносить изменения", })
        else:
            return Response({"error": "patch запрос не предусмотрен", })


class Basket(APIView):
    """
    Класс для просмотра, пополнения и изменения корзины покупателя
    """
    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        if c_type == 'buyer':
            queryset = ProductOrder.objects.filter(order__status="basket", order__user_id=obj.user_id)
            if not queryset:
                return Response({"empty": "Корзина пуста"})
            pk = kwargs.get('pk', None)
            if pk:
                queryset = ProductOrder.objects.get(pk=pk)
                serializer = ProductOrderSerializer(queryset)
            else:
                serializer = ProductOrderSerializer(queryset, many=True)

            return Response(serializer.data)

        else:
            return Response({"error": "У продавца не может быть корзины"})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        if c_type == 'buyer':
            order_id = Order.objects.filter(status="basket", user_id=obj.user_id).first()
            if not order_id:
                order_id = Order.objects.create(user=obj.user, status='basket')
            if {'product_id', 'quantity'}.issubset(request.data):
                try:
                    ProductOrder.objects.update_or_create(order=order_id,
                                                          product_id=request.data['product_id'],
                                                          defaults=dict(quantity=request.data['quantity'], ))
                    return Response({'Status': True})
                except:
                    return Response({'Status': False, 'Errors': 'Неверно указаны аргументы'})
            elif {'order'}.issubset(request.data):
                if request.data['order'].lower() == 'send':
                    order_id.status = 'new'
                    order_id.save()
                    return Response({'Status': True})
                elif request.data['order'].lower() == 'clear':
                    order_id.delete()
                    return Response({'Status': True})
                else:
                    return Response({'Status': False, 'Errors': 'Неверно указаны аргументы'})
            else:
                return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
        else:
            return Response({"error": "продавец не может вносить изменения", })

    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type

        pk = kwargs.get('pk', None)
        if pk:
            if c_type == 'buyer':
                if {'product_id', 'quantity'}.issubset(request.data):
                    try:
                        ProductOrder.objects.filter(pk=pk).update(product_id=request.data['product_id'],
                                                                  quantity=request.data['quantity'])
                        return Response({'Status': True})
                    except:
                        return Response({'Status': False, 'Errors': 'Неверно указаны аргументы'})
            else:
                return Response({"error": "продавец не может вносить изменения", })
        else:
            return Response({"error": "patch запрос не предусмотрен", })

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type

        pk = kwargs.get('pk', None)
        if pk:
            if c_type == 'buyer':
                ProductOrder.objects.get(pk=pk).delete()
                return JsonResponse({'Status': True})
            else:
                return Response({"error": "продавец не может вносить изменения", })
        else:
            return Response({"error": "delete запрос не предусмотрен", })


class UploadPrice(APIView):
    """
    Класс для загрузки прайса от поставщика
    Передать путь в post запросе: "path": "C:\\Users\\User\\Downloads\\price.yml"
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        if c_type != 'supplier':
            return Response({"error": "только поставщик может загружать прайс-лист", })
        if not {'path'}.issubset(request.data):
            return Response({"error": "Необходимо передать путь \"path\" к файлу .yml", })
        path = request.data.get('path')
        print(path)
        try:
            with open(path, "r", encoding="utf-8") as file:
                try:
                    price_dict = upload_yaml(file.read())
                    add_products = add_prod_in_price_list(request, price_dict)
                    print('ок')
                except:
                    print('не верный путь')
                    return Response({"error": "Формат файла должен быть .yml", })
                # print(price_dict)
                print(add_products)
                return Response(add_products)
        except:
            return Response({"error": "Не верно  указан путь к файлу.", })


class CategoryView(APIView):
    """
    Класс для просмотра и создания категорий поставщиком
    """
    # получить данные
    def get(self, request, *args, **kwargs):
        # obj = UserInfo.objects.filter(user__username=request.user).first()
        # c_type = obj.company.counterparty_type
        queryset = Category.objects.all()
        serializer = CategorySerializer(queryset, many=True)

        return Response(serializer.data)

    # Создание категории
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type

        if c_type == 'supplier':
            print(request.data)
            if {"category", "subcategory"}.issubset(request.data):
                try:
                    Category.objects.create(category=request.data.get("category"), subcategory=request.data.get("subcategory"))
                    return Response({'Status': True, 'Success': 'Создана новая категория'})
                except:
                    return Response({"error": "Категория уже существует"})
            else:
                return Response({"error": "Не указаны все необходимые аргументы"})
        else:
            return Response({"error": "покупатель не может вносить изменения", })


class ProductViewSet(viewsets.ModelViewSet):
    """
    Класс для просмотра, добавления, изменения и удаления всех товаров через API
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CategoryProductParametersViewSet(viewsets.ModelViewSet):
    """
    Класс для просмотра, создания, изменения и удаления дополнительных характеристик товара по категориям.
    """
    queryset = ProductParameters.objects.all()
    serializer_class = ProductParametersSerializer
    permission_classes = [IsAuthenticated, IsSupplier]

    def list(self, request, **kwargs):
        # if not request.user.is_authenticated:
        #     return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        # c_type = obj.company.counterparty_type
        # if c_type == 'buyer':
        #     return Response({'Status': False, 'Error': 'Покупатель не может создавать, изменять параметры'}, status=403)
        queryset = ProductParameters.objects.filter(product__supplier_product__company=obj.company)
        serializer = ProductParametersSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, **kwargs):
        # if not request.user.is_authenticated:
        #     return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        # obj = UserInfo.objects.filter(user__username=request.user).first()
        # c_type = obj.company.counterparty_type
        # if c_type == 'buyer':
        #     return Response({'Status': False, 'Error': 'Покупатель не может создавать, изменять параметры'}, status=403)
        queryset = ProductParameters.objects.filter(pk=pk).first()
        serializer = ProductParametersSerializer(queryset)
        return Response(serializer.data)

    # def create(self, request, **kwargs):
    #     if not request.user.is_authenticated:
    #         return Response({'Status': False, 'Error': 'Log in required'}, status=403)
    #     obj = UserInfo.objects.filter(user__username=request.user).first()
    #     c_type = obj.company.counterparty_type
    #     if c_type == 'buyer':
    #         return Response({'Status': False, 'Error': 'Покупатель не может создавать, изменять параметры'}, status=403)
    #
    # def update(self, request, pk=None, **kwargs):
    #     if not request.user.is_authenticated:
    #         return Response({'Status': False, 'Error': 'Log in required'}, status=403)
    #     obj = UserInfo.objects.filter(user__username=request.user).first()
    #     c_type = obj.company.counterparty_type
    #     if c_type == 'buyer':
    #         return Response({'Status': False, 'Error': 'Покупатель не может создавать, изменять параметры'}, status=403)
    #
    # def partial_update(self, request, pk=None, **kwargs):
    #     if not request.user.is_authenticated:
    #         return Response({'Status': False, 'Error': 'Log in required'}, status=403)
    #     obj = UserInfo.objects.filter(user__username=request.user).first()
    #     c_type = obj.company.counterparty_type
    #     if c_type == 'buyer':
    #         return Response({'Status': False, 'Error': 'Покупатель не может создавать, изменять параметры'}, status=403)
    #
    # def destroy(self, request, pk=None, **kwargs):
    #     if not request.user.is_authenticated:
    #         return Response({'Status': False, 'Error': 'Log in required'}, status=403)
    #     obj = UserInfo.objects.filter(user__username=request.user).first()
    #     c_type = obj.company.counterparty_type
    #     if c_type == 'buyer':
    #         return Response({'Status': False, 'Error': 'Покупатель не может создавать, изменять параметры'}, status=403)


class CategoryParametersView(APIView):
    """
        Класс для просмотра всех характеристик, принадлежащих категориям.
        """
    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        pk = kwargs.get('pk', None)
        if pk:
            queryset = CategoryParameters.objects.filter(subcategory_id=pk)
            serializer = CategoryParametersSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            queryset = CategoryParameters.objects.all().order_by('subcategory')
            serializer = CategoryParametersSerializer(queryset, many=True)
            return Response(serializer.data)

    """Test"""
    def post(self, request, *args, **kwargs):
        if {"mail", }.issubset(request.data):
            user = CustomUser.objects.get(username=str(request.user))

            send_mail(f"Hello, {request.user}", request.data.get('mail'), [user.email])
        if {"get_token", }.issubset(request.data):
            verify_user_email(request.user, None)

        if {"token", }.issubset(request.data):
            verify_user_email(request.user, request.data.get("token"))

        return Response({'status': 'ok'})


class SupProducts(APIView):
    """
    Класс для просмотра, пополнения и изменения своих товаров поставщиком, а так же для просмотра покупателем
    всех активных для продажи товаров от поставщиков
    """
    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        if c_type == 'buyer':
            queryset = SupplierProduct.objects.filter(company__sales__activate_sales=True, is_active=True)
        else:
            queryset = SupplierProduct.objects.filter(company=obj.company)
        serializer = SupplierProductSerializer(queryset, many=True)
        pk = kwargs.get('pk', None)
        if pk:
            queryset = SupplierProduct.objects.get(pk=pk)
            serializer = SupplierProductSerializer(queryset)
            mainparams = MainParameters.objects.get(product=queryset.product)
            serializer_param = MainParametersSerializer(mainparams)
            otherparams = ProductParameters.objects.filter(product=queryset.product)
            serializer_othparam = ProductParametersSerializer(otherparams, many=True)

            return Response(serializer.data | {"main_params": serializer_param.data} | {"other_params": serializer_othparam.data})

        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type

        pk = kwargs.get('pk', None)
        if pk:
            return Response({"error": "post запрос не предусмотрен", })
        if c_type == 'buyer':
            return Response({'Status': False, 'Error': 'Только поставщик может добавить товар'}, status=403)
        else:
            if 'product_article_number' in request.data or 'product_id' in request.data:
                article_number = request.data.get('product_article_number')
                product_id = request.data.get('product_id')
                if {"is_active", "quantity", "price", "price_rrc"}.issubset(request.data):
                    if article_number:
                        try:
                            product_id = Product.objects.get(article_number=article_number).id
                        except:
                            return JsonResponse({'Status': False, 'Error': 'Неверный код товара'}, status=403)
                    try:
                        SupplierProduct.objects.update_or_create(product_id=product_id,
                                                                 company=obj.company,
                                                                 defaults={"is_active": request.data.get('is_active'),
                                                                           'quantity': request.data.get('quantity'),
                                                                           'price': request.data.get('price'),
                                                                           'price_rrc': request.data.get('price_rrc'),
                                                                           })
                    except:
                        return Response({'Status': False, 'Errors': 'Неверно указаны аргументы'})
                    return Response({"status": True})
                else:
                    return Response({'Status': False, 'Error': 'Введены не все поля'}, status=403)
            else:
                return Response({'Status': False, 'Error': 'Необходимо ввести артикул либо id товара'}, status=403)


    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type

        pk = kwargs.get('pk', None)
        if pk:
            if c_type == 'buyer':
                return Response({'Status': False, 'Error': 'Только поставщик может обновлять товар'}, status=403)
            else:
                sup_product = SupplierProduct.objects.get(pk=pk)

                sup_product.is_active = request.data.get('is_active', sup_product.is_active)
                sup_product.quantity = request.data.get('quantity', sup_product.quantity)
                sup_product.price = request.data.get('price', sup_product.price)
                sup_product.price_rrc = request.data.get('price_rrc', sup_product.price_rrc)
                sup_product.save()

                return JsonResponse({"status": True})
        else:
            return Response({"error": "patch запрос не предусмотрен", })

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type

        pk = kwargs.get('pk', None)
        if pk:
            if c_type == 'buyer':
                return Response({"error": "покупатель не может вносить изменения", })
            else:
                SupplierProduct.objects.get(pk=pk).delete()
                return JsonResponse({'Status': True})
        else:
            return Response({"error": "delete запрос не предусмотрен", })


class ActivateSalesView(APIView):
    """
    Класс для включения и отключения возможности получать заказов от покупателей поставщику
    """
    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        if c_type == 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Для покупателя данный запрос не предусмотрен'}, status=403)
        else:
            activate_sales = Sales.objects.filter(company=obj.company).first()
        return Response({"is_active": activate_sales.activate_sales})
    # изменить данные
    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        if c_type == 'buyer':
            return Response({'Status': False, 'Error': 'Для покупателя данный запрос не предусмотрен'}, status=403)
        else:
            if "is_active" in request.data:
                if type(request.data.get("is_active")) is bool:
                    Sales.objects.filter(company=obj.company).update(activate_sales=request.data.get("is_active"))
                    return Response({"is_active": request.data.get("is_active")})
                else:
                    return Response({'Status': False, 'Error': 'Значение должно быть true либо false'}, status=403)
            else:
                return Response({'Status': False, 'Error': 'Необходимо ввести ключ "is_active" значение true либо false'}, status=403)
