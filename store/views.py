import os
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView, View, ListView
from django.core.mail import send_mail
from django.template.loader import render_to_string

from Introvert import settings
from .forms import LoginForm, RegistrationForm, CartForm, CourierOrderForm, CDEKOrderForm, \
    PostRuOrderForm, PostWorldOrderForm, SelfOrderForm
from .mixins import CartMixin
from .models import Category, SubCategory, Customer, OrderProduct, Product, Order, Article, parameter
from .utils import reconcile_verb_gender, get_random_session

from yookassa import Configuration, Payment
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from yookassa.domain.notification import WebhookNotification
from django.core.cache import cache


class MyQ(Q):
    default = 'OR'


class WelcomeView(CartMixin, View):

    def get(self, request, *args, **kwargs):

        context = {
            'order': self.order,
            'articles': self.articles,
            'page_role': 'welcome',
        }
        return render(request, 'welcome.html', context)


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        # random_products = Product.randoms.all()
        popular_products = Product.objects.all().order_by('-visits')
        # recently_viewed_products = Product.objects.all().order_by('-last_visit')[0:4]

        context = {
            'categories': self.categories,
            'products': popular_products,
            'order': self.order,
            'page_role': 'products',
            'articles': self.articles,
        }
        return render(request, 'base.html', context)


class GiftListView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        gift_products = Product.objects.filter(gift=True)
        if self.order and self.order.gift:
            messages.add_message(request, messages.INFO,
                                 f'К Вашему заказу уже был добавлен подарок: {self.order.gift.title}')

        context = {
            'bonus_sum': parameter['FREE_GIFT'],
            'categories': self.categories,
            'products': gift_products,
            'order': self.order,
            'page_role': 'gifts',
            'articles': self.articles,
        }
        return render(request, 'gift_list.html', context)


class ProductDetailView(CartMixin, DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'item_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        product = self.get_object()
        product.visits += 1
        product.last_visit = datetime.now()
        product.save()

        product_visits = f'{product.id}_visits'
        product_visits_value = cache.get_or_set(product_visits, product.visits, timeout=60)

        context = super().get_context_data(**kwargs)
        context['categories'] = self.categories
        context['order'] = self.order
        context['articles'] = self.articles
        context['product_views'] = product_visits_value

        return context


class SubCategoryDetailView(CartMixin, DetailView):
    model = SubCategory
    queryset = SubCategory.objects.all()
    context_object_name = 'subcategory'
    template_name = 'subcategory_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subcategory = self.get_object()
        category = Category.objects.get(subcategory=subcategory)
        context['order'] = self.order
        context['category'] = category
        context['categories'] = self.categories
        context['category_name'] = category.name
        context['subcategories'] = self.model.objects.filter(category=category)
        context['subcategory_name'] = subcategory.name
        context['subcategory_products'] = subcategory.product_set.all()
        context['articles'] = self.articles
        return context


class CategoryDetailView(CartMixin, DetailView):
    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    template_name = 'category_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['order'] = self.order
        context['categories'] = self.categories
        context['category_name'] = category.name
        context['subcategories'] = SubCategory.objects.filter(category=category)
        context['category_products'] = category.product_set.all()
        context['articles'] = self.articles
        return context


class ProductSearchView(CartMixin, ListView):
    model = Product
    template_name = 'product_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        context['categories'] = self.categories
        return context

    def get_queryset(self):
        query = self.request.GET.get('p')
        object_list = Product.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        return object_list


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        session = request.COOKIES.get('customersession') or get_random_session()

        customer, created = Customer.objects.get_or_create(session=session)
        if request.user.is_authenticated:
            user = User.objects.get(username=request.user)
            customer.user = user
        customer.save()

        self.order, created = Order.carts.get_or_create(owner=customer)
        if created:
            # Это создание новой корзины. Удалить корзины старше 2 дней
            old_carts = Order.carts.filter(created_at__lte=datetime.now() - timedelta(days=2))
            old_carts.delete()

        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        if product.gift and not self.order.gift and self.order.total_price_net >= parameter['FREE_GIFT']:
            self.order.gift = product
            self.order.save()
            messages.add_message(request, messages.INFO,
                                 f'{product.image_thumb()} К Вашему заказу добавлен подарок: {product}')
        else:
            order_product, created = OrderProduct.objects.get_or_create(
                order=self.order, product=product
            )

            if created:
                self.order.products.add(order_product)
                added_verb = reconcile_verb_gender('добавлен', order_product.product.title)
                messages.add_message(request, messages.INFO, f'{order_product.product.image_thumb()} '
                                                             f'<b>{order_product.product}</b> {added_verb} в корзину')
            else:
                if order_product.product.quantity <= order_product.qty:
                    message = f'{order_product.product.image_thumb()} Количество товара <b>{order_product}</b> ' \
                              f'в корзине {order_product.qty} шт.<br> На складе больше нет, извините!'
                    order_product.qty = order_product.product.quantity
                else:
                    order_product.qty += 1
                    message = f'{order_product.product.image_thumb()} Количество товара <b>{order_product}</b> ' \
                              f'изменено на {order_product.qty} шт.'

                order_product.save()
                messages.add_message(
                    request,
                    messages.INFO,
                    message
                )
            self.order.save()

        response = HttpResponseRedirect(f"/product/{product_slug}/")
        response.set_cookie(key='customersession', value=session)
        return response


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        order_product = OrderProduct.objects.get(
            order=self.order, product=product
        )

        self.order.products.remove(order_product)
        order_product.delete()
        self.order.save()
        removed_verb = reconcile_verb_gender('удален', order_product.product.title)
        messages.add_message(request, messages.INFO,
                             f'{order_product.product.image_thumb()} <b>{order_product}</b> {removed_verb} из корзины')
        return HttpResponseRedirect('/cart/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        order_product = OrderProduct.objects.get(
            order=self.order, product=product
        )
        qty = int(request.POST.get('qty'))
        over = False
        if order_product.product.quantity < qty:
            over = True
            qty = order_product.product.quantity

        if qty:
            order_product.qty = qty
            message = f'{order_product.product.image_thumb()} Количество товара <b>{order_product}</b> изменено на {qty} шт.'
            if over:
                message += '<br>На складе больше нет, извините!'
            messages.add_message(
                request,
                messages.INFO,
                message
            )
            order_product.save()
        else:
            self.order.products.remove(order_product)
            order_product.delete()
            removed_verb = reconcile_verb_gender('удален', order_product.product.title)
            messages.add_message(request, messages.INFO,
                                 f'{order_product.product.image_thumb()} '
                                 f'Из корзины {removed_verb} <b>{order_product}</b>')
        self.order.save()
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = CartForm(request.POST or None)
        if self.order:
            self.order.save()
            if self.order.total_price_net >= parameter['FREE_GIFT'] and not self.order.gift:
                messages.add_message(request, messages.INFO,
                                     f'<a href=/gifts/><img src="/static/img/gift70.png"> Скорее выбери подарок!</a>\n '
                                     f'Сумма товаров в корзине: {self.order.total_price_net}')

        if not self.order or not self.order.products.count():
            messages.add_message(request, messages.INFO,
                                 'Ваша корзина пуста!<br><a href=/store/>Посмотрите наши товары</a>')

        context = {
            'bonus_sum': parameter['FREE_GIFT'],
            'order': self.order,
            'categories': self.categories,
            'form': form,
            'page_role': 'cart',
            'articles': self.articles,
            'free_delivery': parameter['FREE_DELIVERY'],
            'delivery_cdek_cost': parameter['DELIVERY_CDEK_COST'],
            'delivery_courier_cost': parameter['DELIVERY_COURIER_COST'],
            'delivery_ru_cost': parameter['DELIVERY_RU_COST'],
            'delivery_world_cost': parameter['DELIVERY_WORLD_COST'],

        }
        return render(request, 'cart.html', context)


class CheckoutView(CartMixin, View):

    def post(self, request, *args, **kwargs):

        self.order.delivery_type = request.POST.get('delivery_type')
        self.order.save()

        if self.order.delivery_type == 'self':
            form = SelfOrderForm()
        elif self.order.delivery_type == 'delivery_spb':
            form = CourierOrderForm()
        elif self.order.delivery_type == 'delivery_cdekspb':
            form = CDEKOrderForm()
        elif self.order.delivery_type == 'delivery_ru':
            form = PostRuOrderForm()
        elif self.order.delivery_type == 'delivery_world':
            form = PostWorldOrderForm()

        context = {
            'order': self.order,
            'categories': self.categories,
            'form': form,
            'articles': self.articles,
        }

        return render(request, 'checkout.html', context)


class MakeOrderView(LoginRequiredMixin, CartMixin, View):
    login_url = '/login/'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if self.order.delivery_type == 'self':
            form = SelfOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_spb':
            form = CourierOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_cdekspb':
            form = CDEKOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_ru':
            form = PostRuOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_world':
            form = PostWorldOrderForm(request.POST or None)

        user = User.objects.get(username=request.user)
        session = request.COOKIES.get('customersession')

        customer = Customer.objects.get(user=user.id, session=session)
        order = Order.carts.get(owner=customer)

        if form.is_valid():
            if 'first_name' in form.cleaned_data.keys():
                order.first_name = form.cleaned_data['first_name']
            if 'last_name' in form.cleaned_data.keys():
                order.last_name = form.cleaned_data['last_name']
            if 'patronymic' in form.cleaned_data.keys():
                order.patronymic = form.cleaned_data['patronymic']
            if 'phone' in form.cleaned_data.keys():
                order.phone = form.cleaned_data['phone']
            if 'postal_code' in form.cleaned_data.keys():
                order.postal_code = form.cleaned_data['postal_code']
            if 'settlement' in form.cleaned_data.keys():
                order.settlement = form.cleaned_data['settlement']
            if 'address' in form.cleaned_data.keys():
                order.address = form.cleaned_data['address']
            if 'comment' in form.cleaned_data.keys():
                order.comment = form.cleaned_data['comment']

            order.status = 'new'
            order.save()
            if order.delivery_type == 'self':
                order.send_telegram()  # Отправить заказ в телегу

            messages.add_message(request, messages.INFO,
                                 'Ваш заказ оформлен! \nСпасибо, что выбрали нас. Не забудьте оплатить заказ.')
            html = render_to_string('email_order_placed.html', {'user': user, 'order': order, 'site_url': settings.SITE_URL})

            send_mail('Заказ в магазине Интроверт', 'Спасибо за Ваш заказ в магазине Интроверт!',
                      'Интроверт<noreply@introvert.com.ru>', [user.email], fail_silently=False, html_message=html)

            response = HttpResponseRedirect(f'/order_pay/{order.id}/')
            new_session = get_random_session()
            response.set_cookie(key='customersession', value=new_session)
            return response

        return HttpResponseRedirect('/checkout/')


class OrderPayView(LoginRequiredMixin, CartMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        user = User.objects.get(username=request.user)

        order_id = kwargs.get('order')

        try:
            # Отображать заказ только если он принадлежит клиенту - текущему пользователю
            order_to_pay = Order.orders.get(id=order_id, owner__user=user)
            show_pay_button = False if order_to_pay.payment_status in ['succeeded', 'waiting_for_capture'] else True

            return render(
                request,
                'page_payment.html',
                {
                    'show_pay_button': show_pay_button,
                    'order': self.order,
                    'order_to_pay': order_to_pay,
                    'categories': self.categories,
                    'articles': self.articles,
                }
            )
        except:
            messages.add_message(request, messages.INFO,
                                 f'Заказа № {order_id} у вас нет! \nВыберите свой заказ из списка.')
            return HttpResponseRedirect('/profile/')


@method_decorator(csrf_exempt, name='dispatch')
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
            # Установить статусы платежа и, если оплачен, изменить остатки и отправить состав заказа в телегу
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
                Создать сообщение, что товара уже недостаточно и вернуть на страницу товара
                """
                ready_to_pay = False
                item.qty = item.product.quantity
                message = f'{item.product.image_thumb()} Количество товара <b>{item}</b> изменено на {item.qty} шт.' \
                          f'<br>На складе больше нет, извините!'
                messages.add_message(request, messages.INFO, message)
                item.save()
        order_to_pay.save()

        if order_to_pay.gift and order_to_pay.gift.quantity == 0:
            ready_to_pay = False
            message = f'{order_to_pay.gift.image_thumb()} Подарок <b>{order_to_pay.gift}</b> удален из корзины' \
                      f'<br>Этот товар уже раскупили, извините!'
            messages.add_message(request, messages.INFO, message)
            order_to_pay.gift = None

        order_to_pay.save()
        if not ready_to_pay:
            return HttpResponseRedirect('/order_pay/' + str(order_to_pay.id) + '/')

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
                "return_url": f"https://{settings.SITE_URL}/order_pay/{order_to_pay.id}/"
            },
            "capture": True,
            "description": f"Заказ №{order_to_pay.id}"
        })

        # print(payment.__dict__)
        if order_to_pay.init_payment(payment):
            return HttpResponseRedirect(payment.confirmation.confirmation_url)
        else:
            # если заказ уже оплачен (False)
            messages.add_message(request, messages.ERROR,
                                 'Произошла странная ошибка! \nЭтот заказ уже оплачен!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class LoginView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)

        context = {
            'form': form,
            'categories': self.categories,
            'order': self.order,
            'page_role': 'login',
            'articles': self.articles,
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):

        next = request.GET['next'] if request.GET else '/profile/'

        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(
                username=username, password=password
            )
            if user:
                session = request.COOKIES.get('customersession') or get_random_session()
                customer, created = Customer.objects.get_or_create(session=session)

                customer.user = user
                customer.save()

                login(request, user)
                return HttpResponseRedirect(next)

        context = {
            'form': form,
            'order': self.order,
            'categories': self.categories,
            'articles': self.articles,
        }
        return render(request, 'login.html', context)


class RegistrationView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)

        context = {
            'form': form,
            'categories': self.categories,
            'order': self.order,
            'page_role': 'registration',
            'articles': self.articles,
        }
        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):
        session = request.COOKIES.get('customersession')
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.email = form.cleaned_data['email']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            user = authenticate(
                username=new_user.username, password=form.cleaned_data['password']
            )
            login(request, user)
            session = request.COOKIES.get('customersession') or get_random_session()
            customer, created = Customer.objects.get_or_create(session=session)
            if user:
                customer.user = user
            customer.save()

            return HttpResponseRedirect('/cart/')

        context = {
            'form': form,
            'categories': self.categories,
            'order': self.order,
            'articles': self.articles,
        }
        return render(request, 'registration.html', context)


class ProfileView(LoginRequiredMixin, CartMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        owners = Customer.objects.filter(user=request.user)
        orders = Order.orders.filter(owner__in=owners).order_by('-created_at')

        return render(
            request,
            'profile.html',
            {
                'orders': orders,
                'order': self.order,
                'categories': self.categories,
                'page_role': 'profile',
                'articles': self.articles,
            }
        )


class ArticleView(CartMixin, DetailView):
    model = Article
    context_object_name = 'article'
    template_name = 'article_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = self.categories
        context['order'] = self.order
        context['articles'] = self.articles

        return context


class EmailView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

        order_id = kwargs.get('order')

        pay_order = Order.orders.get(id=order_id)

        return render(
            request,
            'email_order_placed.html',
            {
                'site_url': settings.SITE_URL,
                'order': pay_order,
            }
        )
