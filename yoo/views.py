import os
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
import json
from yookassa.domain.notification import WebhookNotification
from store.models import Order
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from Introvert import settings

from yookassa import Configuration, Payment
from store.mixins import CartMixin


class YooStatusView(View):
    """
    Получаем запрос от Юкассы при изменении статуса платежа клиента,
    выковыриваем оттуда статус и сохраняем в Заказ.
    Если статус "succeeded", отправляем телегу со статусом заказа и
    уменьшаем остатки товаров на количество в заказе
    """

    def post(self, request):

        event_json = json.loads(request.body)
        # Cоздайте объект класса уведомлений в зависимости от события
        try:
            notification_object = WebhookNotification(event_json)
            # Получите объекта платежа
            payment = notification_object.object
            order = Order.orders.get(payment_id=payment.id)
            # Установить статусы платежа и, если оплачен, изменить остатки и
            # отправить состав заказа в телегу
            order.register_payment(payment)

            return HttpResponse(status=200)
        except Exception:
            return HttpResponse(status=500)


class BankPaymentView(LoginRequiredMixin, CartMixin, View):
    login_url = '/login/'

    def post(self, request, *args, **kwargs):

        order_id = request.POST.get('order')
        order_to_pay = Order.orders.get(id=order_id)
        ready_to_pay = True

        for item in order_to_pay.related_products.all():
            if item.qty > item.product.quantity:
                """
                Проверить наличие товара из корзины на складе перед оплатой.
                Создать сообщение, что товара уже недостаточно и вернуть
                на страницу товара
                """
                ready_to_pay = False
                item.qty = item.product.quantity
                message = f'{item.product.image_thumb()} Количество товара ' \
                          f'<b>{item}</b> изменено на {item.qty} шт.' \
                          f'<br>На складе больше нет, извините!'
                messages.add_message(request, messages.INFO, message)
                item.save()
        order_to_pay.save()

        if order_to_pay.gift and order_to_pay.gift.quantity == 0:
            ready_to_pay = False
            message = f'{order_to_pay.gift.image_thumb()} ' \
                      f'Подарок <b>{order_to_pay.gift}</b> удален из корзины' \
                      f'<br>Этот товар уже раскупили, извините!'
            messages.add_message(request, messages.INFO, message)
            order_to_pay.gift = None

        order_to_pay.save()
        if not ready_to_pay:
            return HttpResponseRedirect('/order_pay/'
                                        + str(order_to_pay.id) + '/')

        # Configuration.account_id = os.getenv('yoo_shop_id')
        # Configuration.secret_key = os.getenv('yoo_key')
        Configuration.account_id = os.getenv('test_yoo_shop_id')
        Configuration.secret_key = os.getenv('test_yoo_key')

        payment = Payment.create({
            "amount": {
                "value": order_to_pay.total_price_gross,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url":
                    f"https://{settings.SITE_URL}/order_pay/{order_to_pay.id}/"
            },
            "capture": True,
            "description": f"Заказ №{order_to_pay.id}"
        })

        # print(payment.__dict__)
        if order_to_pay.init_payment(payment):
            return HttpResponseRedirect(payment.confirmation.confirmation_url)
        else:
            # если заказ уже оплачен (False)
            messages.add_message(
                request, messages.ERROR,
                'Произошла странная ошибка! \nЭтот заказ уже оплачен!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
