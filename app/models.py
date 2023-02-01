from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.utils.translation import gettext_lazy as _

from retail_service import settings


class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    is_confirmed = models.BooleanField(verbose_name='Подтверждение e-mail', default=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class UserInfo(models.Model):
    user = models.OneToOneField(CustomUser, verbose_name='Пользователь', related_name='users', blank=True, null=True,
                                on_delete=models.CASCADE)
    company = models.ForeignKey("Company", verbose_name='Компания', related_name='users', on_delete=models.CASCADE)
    post = models.CharField(verbose_name='Должность', max_length=30, blank=True)

    class Meta:
        verbose_name = 'Информация о компании'
        verbose_name_plural = "Сотрудники компании"

    def __str__(self):
        return self.user.username


class Company(models.Model):
    C_TYPE = (
        ("buyer", 'Покупатель'),
        ("supplier", 'Поставщик'),
    )
    name = models.CharField(verbose_name='Наименование', max_length=50)
    tin = models.BigIntegerField(verbose_name='ИНН', max_length=12, unique=True)
    counterparty_type = models.CharField(verbose_name='Тип контрагента', choices=C_TYPE, max_length=10, default="buyer")
    description = models.TextField(verbose_name='Описание', blank=True)
    phone_regex = RegexValidator(regex=r'^7\d{10}$',
                                 message="номер телефона в формате 7XXXXXXXXXX (X - цифра от 0 до 9)")
    phone = models.CharField(verbose_name='Номер телефона', validators=[phone_regex], max_length=11, blank=True)
    address = models.CharField(verbose_name='Адрес', max_length=100, blank=True)
    veb_site = models.URLField(verbose_name='Веб сайт', max_length=50, blank=True)


    def save(self, *args, **kwargs):
        self.mobile_operator_code = str(self.phone)[1:4]
        return super(Company, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = "Список компаний"

    def __str__(self):
        return f"{self.name} ИНН:{self.tin}"


class Sales(models.Model):
    activate_sales = models.BooleanField(verbose_name='Активировать получение заказов', default=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='sales', verbose_name='Компания')

    class Meta:
        verbose_name = 'Активировать продажи'
        verbose_name_plural = "Для поставщиков. Включить возможность получать заказы"


class Category(models.Model):
    category = models.CharField(max_length=30, verbose_name='Категория')
    subcategory = models.CharField(max_length=30, verbose_name='Подкатегория')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"
        ordering = ('category',)
        constraints = [
            models.UniqueConstraint(fields=['category', 'subcategory', ], name='unique_subcategory'),
        ]

    def __str__(self):
        return f'{self.category} - {self.subcategory}'


class Product(models.Model):
    name = models.CharField(max_length=30, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    article_number = models.IntegerField(verbose_name='Артикул', unique=True)
    subcategory = models.ForeignKey(Category, verbose_name='Подкатегория', related_name='products',
                                    on_delete=models.CASCADE)

    # main_parameters = models.ForeignKey(MainParameters, verbose_name='Основные характеристики', related_name='products',
    #                                 on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = "Список товаров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class MainParameters(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='main_parameters', on_delete=models.CASCADE,
                                unique=True)
    color = models.CharField(max_length=20, verbose_name='Цвет', blank=True, null=True)
    weight = models.IntegerField(verbose_name='Вес, гр', max_length=10, default=0, blank=True)
    height = models.IntegerField(verbose_name='Высота, мм', max_length=10, default=0, blank=True)
    length = models.IntegerField(verbose_name='Длина, мм', max_length=10, default=0, blank=True)
    width = models.IntegerField(verbose_name='Ширина, мм', max_length=10, default=0, blank=True)
    warranty = models.IntegerField(verbose_name='Гарантия, мес', max_length=10, default=0, blank=True)
    manufacturer = models.CharField(max_length=25, verbose_name='Производитель', blank=True, null=True)
    country = models.CharField(max_length=25, verbose_name='Cтрана изготовитель', blank=True, null=True)

    class Meta:
        verbose_name = 'Общие характеристики'
        verbose_name_plural = "Список характеристик"

    def __str__(self):
        return self.product.name


class SupplierProduct(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='supplier_product',
                                on_delete=models.CASCADE)
    company = models.ForeignKey(Company, verbose_name='Компания-поставщик', related_name='supplier_product',
                                on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name='Товар опубликован (готов к продаже)', default=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество в наличии', default=0)
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')

    class Meta:
        verbose_name = 'Товар поставщика'
        verbose_name_plural = "Товары поставщиков"
        constraints = [
            models.UniqueConstraint(fields=['product', 'company', ], name='unique_supplier_product'),
        ]

    def __str__(self):
        return f"{self.product} - {self.company}"


class CategoryParameters(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=50)
    subcategory = models.ForeignKey(Category, verbose_name='Категории', related_name='parameters',
                                    on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Характеристики по категориям"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameters(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='values', on_delete=models.CASCADE)
    category_parameters = models.ForeignKey(CategoryParameters, verbose_name='Параметр', related_name='values',
                                            on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=50)

    class Meta:
        verbose_name = 'Значение параметра'
        verbose_name_plural = "Характеристики"
        ordering = ('-value',)

    def __str__(self):
        return self.product.name


class Order(models.Model):
    STATUS = (
        ('basket', 'В корзине'),
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('assembled', 'Собран'),
        ('sent', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Пользователь',
                             related_name='orders', blank=True, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', choices=STATUS, max_length=15)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-datetime',)

    def __str__(self):
        return f"Заказ {self.id} - {self.datetime}"


class ProductOrder(models.Model):
    # company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_orders',
    #                             verbose_name='Поставшик', blank=True)
    product = models.ForeignKey(SupplierProduct, verbose_name='Товар', related_name='productorders', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='productorders', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Выбрать товар'
        verbose_name_plural = "Товары"
        constraints = [
            models.UniqueConstraint(fields=['product', 'order', ], name='unique_product_order'),
        ]

    def __str__(self):
        return f"- {self.order} - {self.product}"
