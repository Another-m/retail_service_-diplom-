from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


from app.models import User, SupplierProduct, Sales, UserInfo, ProductOrder, CustomUser, Order
from app.send_message import send_mail



def mail_to(**kwargs):

    if 'all' in kwargs:
        user_list = CustomUser.objects.filter(users__company__counterparty_type=kwargs.get('all'))
        return [i.email for i in user_list]
    if 'company' in kwargs:
        user_list = CustomUser.objects.filter(users__company=kwargs.get('company'))
        return [i.email for i in user_list]
    if 'order' in kwargs:
        order = ProductOrder.objects.filter(order=kwargs.get('order'))
        user_list = CustomUser.objects.filter(users__company__in=[i.product.company for i in order])
        return [i.email for i in user_list]




@receiver(pre_save, sender=SupplierProduct)
def price_update(sender, instance, **kwargs):
    message = f'Поставщик {instance.company} обновил товар в прайс-листе'
    to = mail_to(all='buyers')
    send_mail('Новое у поставщика', message, to)


@receiver(pre_save, sender=Sales)
def active_sales(sender, instance, **kwargs):
    if instance.activate_sales:
        message = f'Поставщик {instance.company} разрешил заказы'
    else:
        message = f'Поставщик {instance.company} установил запрет на заказы'
    to = mail_to(all='buyers')
    send_mail('Новое у поставщика', message, to)


@receiver(pre_save, sender=ProductOrder)
def add_to_basket(sender, instance, **kwargs):
    message = f'{instance.order.user} добавил к себе в корзину товар {instance.product.product}'
    to = mail_to(company=instance.product.company)
    send_mail('Товар в корзине', message, to)

@receiver(pre_save, sender=Order)
def order_status(sender, instance, **kwargs):
    if instance.status == 'new':
        message = f'Заказ № {instance.id} подтвержден покупателем'
        to = mail_to(order=instance)
        send_mail(f"Новый заказ от покупателя {instance.user}", message, to)