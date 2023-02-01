from rest_framework import serializers

from app.models import *


class SalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales
        fields = ["id", "activate_sales", ]
        read_only_fields = ('id',)


class UserInfoSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="user.id", read_only=True)
    user_date_joined = serializers.CharField(source="user.date_joined", read_only=True)
    user_username = serializers.CharField(source="user.username")
    user_email = serializers.CharField(source="user.email")
    user_firstname = serializers.CharField(source="user.first_name", allow_null=True, required=False)
    user_lastname = serializers.CharField(source="user.last_name", required=False)
    company_name = serializers.CharField(source="company.name")
    company_tin = serializers.CharField(source="company.tin")
    company_type = serializers.CharField(source="company.counterparty_type")
    company_description = serializers.CharField(source="company.description", allow_null=True, required=False)
    company_phone = serializers.CharField(source="company.phone", allow_null=True, required=False)
    company_address = serializers.CharField(source="company.address", allow_null=True, required=False)
    company_veb_site = serializers.CharField(source="company.veb_site", allow_null=True, required=False)

    class Meta:
        model = UserInfo
        fields = ("user_id", 'user_date_joined', 'user_username', "user_email", "user_firstname", 'user_lastname',
                  "company_id", "company_name", "company_tin", "company_type", "company_description", "company_phone",
                  "company_address", "company_veb_site", "post", )
        # fields = ('id', 'user_id', 'company_id', 'post', 'user_date_joined')
        read_only_fields = ('id',)

    def create(self, validated_data):
        if {'user', }.issubset(validated_data):
            user_data = validated_data.get('user')
            user = CustomUser.objects.create(**user_data)
        if {'company', }.issubset(validated_data):
            company_data = validated_data.get('company')
            company = Company.objects.create(**company_data)
        if {'user', 'company', 'post', }.issubset(validated_data):
            user_data = validated_data.get('post')
            UserInfo.objects.create(user=user, company=company,post=user_data)

        # new_user = super().create(validated_data)
        # return new_user
        return user

    def update(self, instance, validated_data):

        if {'user', }.issubset(validated_data):
            user_data = validated_data.get('user')
            instance.user.username = user_data.get('username', instance.user.username)
            instance.user.email = user_data.get('email', instance.user.email)
            instance.user.first_name = user_data.get('first_name', instance.user.first_name)
            instance.user.last_name = user_data.get('last_name', instance.user.last_name)
            instance.user.password = user_data.get('password', instance.user.password)
            instance.user.save()

        if {'company', }.issubset(validated_data):
            company_data = validated_data.get('company')
            instance.company.name = company_data.get('name', instance.company.name)
            instance.company.tin = company_data.get('tin', instance.company.tin)
            instance.company.counterparty_type = company_data.get('counterparty_type', instance.company.counterparty_type)
            instance.company.description = company_data.get('description', instance.company.description)
            instance.company.phone = company_data.get('phone', instance.company.phone)
            instance.company.address = company_data.get('address', instance.company.address)
            instance.company.veb_site = company_data.get('veb_site', instance.company.veb_site)
            instance.company.save()

        instance.post = validated_data.get('post', instance.post)
        instance.save()
        return instance


class OrderSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField('get_count')
    total = serializers.SerializerMethodField('get_total_sum')

    def get_count(self, instance):
        return instance.count

    def get_total_sum(self, instance):
        return instance.total

    class Meta:
        model = Order
        fields = ("id", 'datetime', "status", 'count', "total", )
        # fields = '__all__'
        read_only_fields = ('id',)


class OrdersSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ("id", 'datetime', "status", )
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        # fields = ('id', 'name', 'value')
        fields = "__all__"
        read_only_fields = ('id',)


class MainParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainParameters
        fields = "__all__"
        # fields = ('id', 'name', )
        read_only_fields = ('id', 'product')


class ProductParametersSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="category_parameters.name")
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductParameters
        fields = ('id', 'name', 'value', 'product', 'product_name')
        # fields = "__all__"
        read_only_fields = ('id',)

    def create(self, validated_data):
        category = Category.objects.get(id=validated_data.get('product').subcategory.id)
        id_param = CategoryParameters.objects.filter(subcategory=category,
                                                     name=validated_data['category_parameters'].get('name')).first()
        if not id_param:
            id_param = CategoryParameters.objects.create(subcategory=category,
                                                         name=validated_data['category_parameters'].get('name'))
        validated_data['category_parameters'] = id_param
        new_param = super().create(validated_data)
        return new_param

    def update(self, instance, validated_data):
        if 'category_parameters' in validated_data:
            validated_data.pop('category_parameters')
        if 'product' in validated_data:
            validated_data.pop('product')
        param = super().update(instance, validated_data)
        return param


class CategoryParametersSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="subcategory", read_only=True)
    values = ProductParametersSerializer(many=True, required=False)
    class Meta:
        model = CategoryParameters
        fields = ('subcategory', 'category_name', 'name', 'values')
        # fields = "__all__"
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="subcategory", read_only=True)
    main_parameters = MainParametersSerializer(many=True, required=False)

    class Meta:
        model = Product
        # fields = "__all__"
        fields = ["id", "name", "description", "article_number", "subcategory", "category_name", "main_parameters", ]
        read_only_fields = ('id', )

    def create(self, validated_data):
        if 'main_parameters' in validated_data:
            main_parameters_data = validated_data.pop('main_parameters')
            product = super().create(validated_data)
            for element in range(len(main_parameters_data)):
                MainParameters.objects.create(product=product, **main_parameters_data[element])
        else:
            product = super().create(validated_data)
            MainParameters.objects.create(product=product,
                                          color=None,
                                          weight=0,
                                          height=0,
                                          length=0,
                                          width=0,
                                          warranty=0,
                                          manufacturer=None,
                                          country=None
                                          )
        return product

    def update(self, instance, validated_data):
        if 'main_parameters' in validated_data:
            main_parameters_data = validated_data.pop('main_parameters')
            product = super().update(instance, validated_data)
            for value in main_parameters_data:
                params = MainParameters.objects.filter(product=product)
                params.update(color=value.get('color', params.first().color),
                              weight=value.get('weight', params.first().weight),
                              height=value.get('height', params.first().height),
                              length=value.get('length', params.first().length),
                              width=value.get('width', params.first().width),
                              warranty=value.get('warranty', params.first().warranty),
                              manufacturer=value.get('manufacturer', params.first().manufacturer),
                              country=value.get('country', params.first().country)
                              )
        else:
            product = super().update(instance, validated_data)
        return product



class SupplierProductSerializer(serializers.ModelSerializer):
    company = serializers.StringRelatedField()
    # product_id = serializers.CharField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_description = serializers.CharField(source="product.description", read_only=True)
    product_article_number = serializers.CharField(source="product.article_number", read_only=True)
    product_category_id = serializers.CharField(source="product.subcategory.id", read_only=True)
    product_category = serializers.CharField(source="product.subcategory.category", read_only=True)
    product_subcategory = serializers.CharField(source="product.subcategory.subcategory", read_only=True)
    # main_parameters = MainParametersSerializer(read_only=True, many=True)

    class Meta:
        model = SupplierProduct
        # fields = "__all__"
        fields = ["id", "company", "product_id",  "product_name", "product_description", "product_article_number",
                  "product_name", "product_category_id", "product_category", "product_subcategory", "is_active",
                  "quantity", "price", "price_rrc", ]
        read_only_fields = ('id',)


class ProductOrderSerializer(serializers.ModelSerializer):
    # order = ItemOrderSerializer(many=
    user_id = serializers.CharField(source="order.user.id", read_only=True)
    user_username = serializers.CharField(source="order.user.username", read_only=True)
    user_email = serializers.CharField(source="order.user.email", read_only=True)
    user_firstname = serializers.CharField(source="order.user.first_name", read_only=True)
    order_status = serializers.CharField(source="order.status", allow_null=True, required=False)
    order_datetime = serializers.CharField(source="order.datetime", read_only=True)
    product_name = serializers.CharField(source="product.product.name", read_only=True)
    product_description = serializers.CharField(source="product.product.description", read_only=True)
    product_article_number = serializers.CharField(source="product.product.article_number", read_only=True)
    product_price = serializers.CharField(source="product.price", read_only=True)


    class Meta:
        model = ProductOrder
        fields = ["id", "user_id", 'user_username', "user_email", "user_firstname", "order_id", "order_status",
                  "order_datetime", "product_id", "product_name", "product_description", "product_article_number",
                  "product_price", "quantity"]
        read_only_fields = ('id',)
