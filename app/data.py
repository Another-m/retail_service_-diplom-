from django.contrib import messages
from django.db.models import Sum, Count, F
from django.contrib.auth.tokens import  default_token_generator

from app.loading_files import upload_yaml
from app.models import *
from app.send_message import send_mail



def get_user(username):
    user = CustomUser.objects.filter(username=username).first()
    return user


def create_company(data):
    try:
        company = Company.objects.create(name=data['company'], tin=data['tin'],
                                         counterparty_type=data['counterparty_type'])
    except:
        company = Company.objects.filter(tin=data['tin']).first()
    user = CustomUser.objects.filter(username=data['username']).first()
    userinfo = UserInfo(post=data['post'], user=user, company=company)
    userinfo.save()
    return


def update_user(data_request, username):
    try:
        CustomUser.objects.filter(username=username).update(**{data_request.get('change'): data_request.get('value')})
    except:
        user = CustomUser.objects.filter(username=username).first()
        try:
            UserInfo.objects.filter(user=user).update(**{data_request.get('change'): data_request.get('value')})
        except:
            Company.objects.filter(pk=user.users.company.id).update(**{data_request.get('change'): data_request.get('value')})


def filter_products(request, *args):
    products = SupplierProduct.objects.filter(company__sales__activate_sales=True, is_active=True)
    if len(args) == 1:
        products = products.filter(product__subcategory__category=args[0])
    if len(args) == 2:
        products = products.filter(product__subcategory__subcategory=args[1])
    if 'seller' in request.GET:
        products = products.filter(company__id__in=dict(request.GET)['seller'])
    return products

def get_filters(request, *args):
    filters = dict(categories=dict(name="Категории", items=[]), suppliers=dict(name="Поставщики", items=[]), )
    if len(args) == 1:
        filters['categories']['items'] = Category.objects.filter(category=args[0])
        category = dict(supplier_product__product__subcategory__category=args[0])
    elif len(args) == 0:
        filters['categories']['items'] = Category.objects.values('category').distinct()
        category = dict()
    else:
        category = dict(supplier_product__product__subcategory__subcategory=args[1])
    filters['suppliers']['items'] = Company.objects.filter(counterparty_type='supplier', **category).values('name', 'id').distinct()
    if 'seller' in request.GET:
        filters['suppliers']['selected_suppliers'] = dict(request.GET)['seller']
    else:
        filters['suppliers']['selected_suppliers'] = [str(i['id']) for i in filters['suppliers']['items']]
    filters['filter_supp'] = ''
    if filters['suppliers']['selected_suppliers']:
        filters['filter_supp'] = ''.join([f'&seller={i}' for i in filters['suppliers']['selected_suppliers']])

    return filters


def get_order(order_id):
    products = ProductOrder.objects.filter(order__id=order_id).order_by('pk')
    return products


def get_orders(username, dates):
    user = CustomUser.objects.filter(username=username).first()
    products = SupplierProduct.objects.filter(company=user.users.company)
    if dates.get('date') == "all":
        interval = 'за всё время'
        if user.users.company.counterparty_type == 'buyer':
            orders = Order.objects.filter(user=user).annotate(total=Sum('productorders__product__price'),
                                                              count=Count('productorders__product__price')).order_by('id')
        else:
            orders = ProductOrder.objects.filter(product__in=[i.id for i in products])
    else:
        if dates.get('date_from') and dates.get('date_to'):
            interval = f"c {dates.get('date_from')} по {dates.get('date_to')}"
            if user.users.company.counterparty_type == 'buyer':
                orders = Order.objects.filter(user=user, datetime__range=(dates.get('date_from'),
                                                                          dates.get('date_to') + " 23:59")
                                              ).annotate(total=Sum('productorders__product__price'),
                                                         count=Count('productorders__product__price')).order_by('id')
            else:
                orders = ProductOrder.objects.filter(product__in=[i.id for i in products],
                                                     order__datetime__range=(
                                                         dates.get('date_from'), dates.get('date_to') + " 23:59"))
        else:
            orders = []
            interval = "не выбрано"
    return dict(orders=orders, interval=interval)


def update_order(date):
    order = Order.objects.get(pk=date.get('change'))
    order.status = date.get('status')
    order.save()
    return dict(orders=list[order], interval=order.datetime)


# Добавление, изменение данных при наличии параметров в запросе
def request_params(request, order_id):
    username = str(request.user)
    if request.method == 'GET':
        choose_params = request.GET.get("choose")
        quantity_params = request.GET.get("quantity")
    elif request.method == 'POST':
        choose_params = request.POST.get("choose")
        quantity_params = request.POST.get("quantity")
    # del request.session['basket']
    if choose_params:
        if order_id == 0:
            if 'basket' in request.session:
                order_id = request.session.get('basket')
            else:
                orders = Order.objects.filter(user__username=username, status='basket').first()
                if orders:
                    order_id = orders.id
                    request.session['basket'] = orders.id
                else:
                    user_id = CustomUser.objects.get(username=username)
                    new_order = Order.objects.create(status="basket", user=user_id)
                    order_id = new_order.id
                    request.session['basket'] = new_order.id

        if "del" in request.GET:
            dell_product(choose_params)
        else:
            choose_items(order_id, choose_params, quantity_params)
    count = count_products(order_id)
    return count


# Выбор товаров и добавление в корзину либо изменение количества, если товар есть в корзине
def choose_items(order_id, product_id, quantity):
    order = ProductOrder.objects.update_or_create(order_id=order_id, product_id=product_id, defaults={'quantity': quantity})


# Удаление товара из корзины
def dell_product(position_id):
    posution = ProductOrder.objects.get(pk=position_id)
    posution.delete()


# Удаление заказа
def dell_order(request, order_id):
    order = Order.objects.get(pk=order_id)
    if order.user.username == str(request.user) and order.status == 'basket':
        order.delete()
        return True


def count_products(order_id):
    if not order_id:
        return dict(count=0, main_sum=0)
    products = ProductOrder.objects.filter(order__id=order_id)
    count = products.aggregate(Sum('quantity'))
    main_sum = products.aggregate(total=Sum(F('product__price') * F('quantity')))['total']
    return dict(count=count['quantity__sum'], main_sum='{0:,}'.format(main_sum).replace(',', ' '))


def get_product(article_number, request):
    data = dict()
    products = SupplierProduct.objects.filter(product__article_number=article_number)
    my_product = products.filter(company__users__user__username=str(request.user))
    if my_product:
        data['products'] = my_product.first()
        data['is_exist'] = True
    else:
        data['is_exist'] = False
        data['products'] = products.first()
        if not products:
            products = Product.objects.filter(article_number=article_number).first()
            data['products'] = SupplierProduct(product=products)
            print(data['products'].product.name)
    data['main_parameters'] = MainParameters.objects.filter(product=data['products'].product).first()
    data['other_parameters'] = ProductParameters.objects.filter(product=data['products'].product.id)
    data['category_parameters'] = CategoryParameters.objects.filter(subcategory=data['products'].product.subcategory)
    return data


def add_product(request, article_number):
    options_to_choose = dict()
    if 'file' in request.FILES:
        file = request.FILES.get('file')
        try:
            price_dict = upload_yaml(file.read())
            add_products = add_prod_in_price_list(request, price_dict)
        except:
            messages.error(request, 'Формат файла должен быть yml.')
            add_products = {}

        if {'error'}.issubset(add_products):
            messages.error(request, add_products['error'])
        elif {'success'}.issubset(add_products):
            messages.success(request, add_products['success'])

    elif 'file' in request.POST:
        messages.error(request, 'Файл не выбран')
        return options_to_choose


    elif 'other' in request.POST:
        options_to_choose['subcategories'] = Category.objects.filter(category=request.POST.get('category'))
        if 'subcategory' in request.POST:
            options_to_choose['products'] = Product.objects.filter(subcategory__subcategory=request.POST.get('subcategory'))
            if 'article_number' in request.POST:
                products = SupplierProduct.objects.filter(product__article_number=request.POST.get('article_number'),
                                                          company__users__user__username=str(request.user)).first()
                if products:
                    options_to_choose['products'] = products
                    options_to_choose['is_exist'] = "Выбранный товар уже есть в Вашем прайс-листе"
                else:
                    product = Product.objects.filter(article_number=article_number).first()
                    options_to_choose['products'] = SupplierProduct(product=product)
    else:
        product = Product.objects.filter(article_number=article_number).first()
        if 'article_number' in request.POST:
            try:
                Category.objects.update_or_create(category=request.POST.get('category'),
                                                  defaults={'subcategory': request.POST.get('subcategory')})
            except: pass
            finally:
                subcategory = Category.objects.filter(category=request.POST.get('category'), subcategory=request.POST.get('subcategory')).first()
            company = Company.objects.filter(users__user__username=str(request.user)).first()
            Product.objects.update_or_create(article_number=request.POST.get('article_number'),
                                             defaults=dict(subcategory=subcategory,
                                                           name=request.POST.get('product'),
                                                           description=request.POST.get('description'),
                                                           ))
            if not product:
                product = Product.objects.filter(article_number=article_number).first()
            SupplierProduct.objects.update_or_create(product=product,
                                                     company=company,
                                                     defaults={'quantity': request.POST.get('quantity'),
                                                               'price': request.POST.get('price'),
                                                               'price_rrc': request.POST.get('price_rrc'),
                                                               })
        if 'is_active' in request.POST:
            if 'active_ok' in request.POST:
                SupplierProduct.objects.filter(product=product,
                                               company__users__user__username=str(request.user)
                                               ).update(is_active=True,
                                                        )
            else:
                SupplierProduct.objects.filter(product=product,
                                               company__users__user__username=str(request.user)
                                               ).update(is_active=False,
                                                        )
        if 'color' in request.POST:
            MainParameters.objects.update_or_create(product=product,
                                                    defaults={'color': request.POST.get('color'),
                                                              'weight': request.POST.get('weight'),
                                                              'height': request.POST.get('height'),
                                                              'length': request.POST.get('length'),
                                                              'width': request.POST.get('width'),
                                                              'warranty': request.POST.get('warranty'),
                                                              'manufacturer': request.POST.get('manufacturer'),
                                                              'country': request.POST.get('country'),
                                                              })
        if 'other_param' in request.POST:
            if 'delete' in request.POST:
                ProductParameters.objects.get(pk=request.POST.get('delete')).delete()
            else:
                ProductParameters.objects.filter(category_parameters_id=request.POST.get('other_param'),
                                                 # category_parameters__subcategory_id=request.POST.get('subcategory_id'),
                                                 product=product,
                                                 ).update(value=request.POST.get('value_param'),
                     )
        options_to_choose = get_product(article_number, request)

        if 'new_param' in request.POST:
            if request.POST.get('new_param'):
                add_parameters(request.POST.get('new_param'), request.POST.get('value'), options_to_choose['products'])

    return options_to_choose

def add_prod_in_price_list(request, price_dict):
    company = Company.objects.filter(users__user__username=str(request.user)).first()
    if price_dict['company'] == company.name:
        count_add = 0
        count_update = 0
        params_list = ''
        for product in price_dict['products']:
            try:
                cat = Category.objects.create(category=product['category']['category'],
                                              subcategory=product['category']['subcategory'],
                                              )
            except:
                cat = Category.objects.filter(category=product['category']['category'],
                                              subcategory=product['category']['subcategory'],
                                              ).first()
            try:
                prod = Product.objects.create(article_number=product['article_number'],
                                              name=product['name'],
                                              subcategory=cat,
                                              description=product['description'],
                                              )
                SupplierProduct.objects.create(product=prod,
                                               company=company,
                                               price=product['price'],
                                               price_rrc=product['price_rrc'],
                                               quantity=product['quantity'],
                                               )
                count_add += 1
            except:
                prod = Product.objects.filter(article_number=product['article_number']).first()
                try:
                    SupplierProduct.objects.create(product=prod,
                                                   company=company,
                                                   price=product['price'],
                                                   price_rrc=product['price_rrc'],
                                                   quantity=product['quantity'],
                                                   )
                    count_add += 1
                except:
                    SupplierProduct.objects.filter(product=prod,
                                                   company=company).update(
                        price=product['price'],
                        price_rrc=product['price_rrc'],
                        quantity=product['quantity'],
                    )
                    count_update += 1
            if 'main_params' in product:
                product_param = product['main_params']
                main_params = MainParameters.objects.filter(product=prod).first()
                if not main_params:
                    main_params = MainParameters.objects.create(product=prod)

                main_params.color = product_param.get('color', main_params.color)
                main_params.weight = product_param.get('weight', main_params.weight)
                main_params.height = product_param.get('height', main_params.height)
                main_params.length = product_param.get('length', main_params.length)
                main_params.width = product_param.get('width', main_params.width)
                main_params.warranty = product_param.get('warranty', main_params.warranty)
                main_params.manufacturer = product_param.get('manufacturer', main_params.manufacturer)
                main_params.country = product_param.get('country', main_params.country)
                main_params.save()
            else:
                params_list += f"{product['name']} ({product['article_number']}), "
            if 'parameters' in product:
                for y in product['parameters'].items():
                    add_parameters(y[0], y[1], SupplierProduct(product=prod))

        if params_list:
            return {'error': f'\nВы забыли добавить характеристики к товарам: {params_list}'}
    else:
        return {'error': 'Прайс не сохранен. Наименование компании не совпадает.'}



    return {'success': f'Прайс успешно загружен. Добавлены {count_add} новых товаров и {count_update} были обновлены.'}


def add_parameters(key, value, product):
    param_name = CategoryParameters.objects.filter(name=key,
                                                   subcategory__subcategory=product.product.subcategory.subcategory).first()
    if param_name:
        ProductParameters.objects.update_or_create(product=product.product,
                                                   category_parameters=param_name,
                                                   defaults={'value': value})
    else:
        cp = CategoryParameters.objects.create(name=key, subcategory=product.product.subcategory)
        ProductParameters.objects.create(product=product.product, value=value, category_parameters=cp)


def verify_user_email(username, token):
    user = CustomUser.objects.filter(username=username)
    if token:
        is_checked = default_token_generator.check_token(user.first(), token)
        user.update(is_confirmed=True)
        return is_checked
    else:
        token = default_token_generator.make_token(user.first())
        url = f'Для подтверждения Вашего e-mail, пройдите по ссылке http://127.0.0.1:8000/confirmation/{username}/{token}'
        send_mail("Подтверждение регистрации", url, [user.first().email])
        return url
