# Generated by Django 4.0.6 on 2022-10-21 20:10

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=30, verbose_name='Категория')),
                ('subcategory', models.CharField(max_length=30, verbose_name='Подкатегория')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Список категорий',
                'ordering': ('category',),
            },
        ),
        migrations.CreateModel(
            name='CategoryParameters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Наименование')),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='app.category', verbose_name='Категории')),
            ],
            options={
                'verbose_name': 'Параметр',
                'verbose_name_plural': 'Характеристики по категориям',
                'ordering': ('-name',),
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Наименование')),
                ('tin', models.BigIntegerField(max_length=12, unique=True, verbose_name='ИНН')),
                ('counterparty_type', models.CharField(choices=[('buyer', 'Покупатель'), ('supplier', 'Поставщик')], default='buyer', max_length=10, verbose_name='Тип контрагента')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('phone', models.CharField(blank=True, max_length=11, validators=[django.core.validators.RegexValidator(message='номер телефона в формате 7XXXXXXXXXX (X - цифра от 0 до 9)', regex='^7\\d{10}$')], verbose_name='Номер телефона')),
                ('address', models.CharField(blank=True, max_length=100, verbose_name='Адрес')),
                ('veb_site', models.URLField(blank=True, max_length=50, verbose_name='Веб сайт')),
            ],
            options={
                'verbose_name': 'Компания',
                'verbose_name_plural': 'Список компаний',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('basket', 'В корзине'), ('new', 'Новый'), ('confirmed', 'Подтвержден'), ('assembled', 'Собран'), ('sent', 'Отправлен'), ('delivered', 'Доставлен'), ('canceled', 'Отменен')], max_length=15, verbose_name='Статус')),
                ('user', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
                'ordering': ('-datetime',),
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='Название')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('article_number', models.IntegerField(unique=True, verbose_name='Артикул')),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='app.category', verbose_name='Подкатегория')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Список товаров',
                'ordering': ('-name',),
            },
        ),
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post', models.CharField(blank=True, max_length=30, verbose_name='Должность')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='app.company', verbose_name='Компания')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Информация о компании',
                'verbose_name_plural': 'Сотрудники компании',
            },
        ),
        migrations.CreateModel(
            name='SupplierProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='Товар опубликован (готов к продаже)')),
                ('quantity', models.PositiveIntegerField(verbose_name='Количество в наличии')),
                ('price', models.PositiveIntegerField(verbose_name='Цена')),
                ('price_rrc', models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_product', to='app.company', verbose_name='Компания-поставщик')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_product', to='app.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Товар поставщика',
                'verbose_name_plural': 'Товары поставщиков',
            },
        ),
        migrations.CreateModel(
            name='Sales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activate_sales', models.BooleanField(default=True, verbose_name='Активировать получение заказов')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='app.company', verbose_name='Компания')),
            ],
            options={
                'verbose_name': 'Активировать продажи',
                'verbose_name_plural': 'Для поставщиков. Включить возможность получать заказы',
            },
        ),
        migrations.CreateModel(
            name='ProductParameters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=50, verbose_name='Значение')),
                ('category_parameters', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='app.categoryparameters', verbose_name='Параметр')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='app.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Значение параметра',
                'verbose_name_plural': 'Характеристики',
                'ordering': ('-value',),
            },
        ),
        migrations.CreateModel(
            name='ProductOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Количество')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productorders', to='app.order', verbose_name='Заказ')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productorders', to='app.supplierproduct', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Выбрать товар',
                'verbose_name_plural': 'Товары',
            },
        ),
        migrations.CreateModel(
            name='MainParameters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(blank=True, max_length=20, null=True, verbose_name='Цвет')),
                ('weight', models.IntegerField(blank=True, max_length=10, null=True, verbose_name='Вес, гр')),
                ('height', models.IntegerField(blank=True, max_length=10, null=True, verbose_name='Высота, мм')),
                ('length', models.IntegerField(blank=True, max_length=10, null=True, verbose_name='Длина, мм')),
                ('width', models.IntegerField(blank=True, max_length=10, null=True, verbose_name='Ширина, мм')),
                ('warranty', models.IntegerField(blank=True, max_length=10, null=True, verbose_name='Гарантия, мес')),
                ('manufacturer', models.CharField(blank=True, max_length=25, null=True, verbose_name='Производитель')),
                ('country', models.CharField(blank=True, max_length=25, null=True, verbose_name='Cтрана изготовитель')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='main_parameters', to='app.product', unique=True, verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Общие характеристики',
                'verbose_name_plural': 'Список характеристик',
            },
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(fields=('category', 'subcategory'), name='unique_subcategory'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.AddConstraint(
            model_name='supplierproduct',
            constraint=models.UniqueConstraint(fields=('product', 'company'), name='unique_supplier_product'),
        ),
        migrations.AddConstraint(
            model_name='productorder',
            constraint=models.UniqueConstraint(fields=('product', 'order'), name='unique_product_order'),
        ),
    ]