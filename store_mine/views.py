from datetime import datetime, timedelta

from django.contrib import messages
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
    PostRuOrderForm, PostWorldOrderForm, PaymentMethodForm, SelfOrderForm, PaymentForm, OnlinePaymentForm
from .mixins import CartMixin
from .models import Category, SubCategory, Customer, OrderProduct, Product, Order, Article, parameter
from .utils import reconcile_verb_gender, get_random_session


class MyQ(Q):
    default = 'OR'


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        random_products = Product.randoms.all()
        # popular_products = Product.objects.all().order_by('-visits')
        # recently_viewed_products = Product.objects.all().order_by('-last_visit')[0:4]

        context = {
            'categories': categories,
            'products': random_products,
            'order': self.order,
            'page_role': 'products',
            'articles': self.articles,
        }
        return render(request, 'base.html', context)


class GiftListView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        gift_products = Product.objects.filter(gift=True)
        context = {
            'bonus_sum': parameter['FREE_GIFT'],
            'categories': categories,
            'products': gift_products,
            'order': self.order,
            'page_role': 'gifts',
            'articles': self.articles,
        }
        return render(request, 'gift_list.html', context)


class ProductDetailView(CartMixin, DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        product = self.get_object()
        product.visits += 1
        product.last_visit = datetime.now()
        product.save()

        context = super().get_context_data(**kwargs)
        context['categories'] = self.get_object().category.__class__.objects.all()
        context['order'] = self.order
        context['articles'] = self.articles

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
        context['categories'] = Category.objects.all()
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
        context['categories'] = self.model.objects.all()
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
        context['categories'] = Category.objects.all()
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
                order_product.qty += 1
                order_product.save()
                messages.add_message(
                    request,
                    messages.INFO,
                    f'{order_product.product.image_thumb()} '
                    f'Количество товара <b>{order_product}</b> изменено на {order_product.qty} шт.'
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

        if qty:
            order_product.qty = qty
            messages.add_message(
                request,
                messages.INFO,
                f'{order_product.product.image_thumb()} Количество товара <b>{order_product}</b> изменено на {qty} шт.'
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
        categories = Category.objects.all()
        form = CartForm(request.POST or None)
        if self.order:
            self.order.save()
            if self.order.total_price_net >= parameter['FREE_GIFT'] and not self.order.gift:
                messages.add_message(request, messages.INFO,
                                     f'<a href=/gifts/><img src="/static/img/gift70.png"> Скорее выбери подарок!</a>\n '
                                     f'Сумма товаров в корзине: {self.order.total_price_net}')

        context = {
            'bonus_sum': parameter['FREE_GIFT'],
            'order': self.order,
            'categories': categories,
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
            form_pay = PaymentForm()
        elif self.order.delivery_type == 'delivery_spb':
            form = CourierOrderForm()
            form_pay = OnlinePaymentForm()
        elif self.order.delivery_type == 'delivery_cdekspb':
            form = CDEKOrderForm()
            form_pay = OnlinePaymentForm()
        elif self.order.delivery_type == 'delivery_ru':
            form = PostRuOrderForm()
            form_pay = OnlinePaymentForm()
        elif self.order.delivery_type == 'delivery_world':
            form = PostWorldOrderForm()
            form_pay = OnlinePaymentForm()

        categories = Category.objects.all()
        context = {
            'order': self.order,
            'categories': categories,
            'form': form,
            'form_pay': form_pay,
            'articles': self.articles,
        }

        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if self.order.delivery_type == 'self':
            form = SelfOrderForm(request.POST or None)
            form_pay = PaymentForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_spb':
            form = CourierOrderForm(request.POST or None)
            form_pay = OnlinePaymentForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_cdekspb':
            form = CDEKOrderForm(request.POST or None)
            form_pay = OnlinePaymentForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_ru':
            form = PostRuOrderForm(request.POST or None)
            form_pay = OnlinePaymentForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_world':
            form = PostWorldOrderForm(request.POST or None)
            form_pay = OnlinePaymentForm(request.POST or None)

        user = User.objects.get(username=request.user)
        session = request.COOKIES.get('customersession')

        customer = Customer.objects.get(user=user.id, session=session)
        order = Order.carts.get(owner=customer)

        if form.is_valid() and form_pay.is_valid():
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
            if 'payment_type' in form_pay.cleaned_data.keys():
                order.payment_type = form_pay.cleaned_data['payment_type']

            order.status = 'new'
            order.save()

            messages.add_message(request, messages.INFO,
                                 'Ваш заказ оформлен! \nСпасибо, что выбрали нас.')

            teleg = 'Новый заказ introvert.com.ru\n'  # Текст для телеграма

            for item in order.products.all():
                teleg += f"- {item}, {item.qty} шт\n"
            if order.gift:
                teleg += f"- Подарок: {order.gift}\n"
            teleg += f"Итого: {order.total_price_gross} р\n"
            teleg += f"{dict(order.DELIVERY_TYPE_CHOICES)[order.delivery_type]}\n"
            if order.delivery_type.startswith('delivery'):
                teleg += f"{order.address}\n{order.settlement} {order.postal_code}\n"

            Order.send_telegram(teleg)
            html = render_to_string('order_placed.html', {'user': user, 'order': order, 'site_url': settings.SITE_URL})

            send_mail('Заказ в магазине Интроверт', 'Спасибо за Ваш заказ в магазине Интроверт!',
                      'Интроверт<noreply@introvert.com.ru>', [user.email], fail_silently=False, html_message=html)

            response = HttpResponseRedirect(f'/order_pay/{order.id}/')
            new_session = get_random_session()
            response.set_cookie(key='customersession', value=new_session)
            return response

        return HttpResponseRedirect('/checkout/')


class PayView(CartMixin, View):
    """
    TODO: Не показывать чужие заказы. Проверять принадлежит ли заказ юзеру.
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

        form = PaymentMethodForm(request.POST or None)
        order_id = kwargs.get('order')

        order_to_pay = Order.orders.get(id=order_id)

        categories = Category.objects.all()
        return render(
            request,
            'page_payment.html',
            {
                'order': self.order,
                'form': form,
                'order_to_pay': order_to_pay,
                'categories': categories,
                'articles': self.articles,
            }
        )


class BankPayView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        order_id = request.POST.get('order')
        print(request.POST)
        return HttpResponse('<a href=/>Home</a><br>Форма платежной системы. Bank Payment. Order ' + str(order_id))


class LoginView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'order': self.order,
            'page_role': 'login',
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):

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
                return HttpResponseRedirect('/cart/')
        categories = Category.objects.all()
        context = {
            'form': form,
            'order': self.order,
            'categories': categories,
            'articles': self.articles,
        }
        return render(request, 'login.html', context)


class RegistrationView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
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
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'order': self.order,
            'articles': self.articles,
        }
        return render(request, 'registration.html', context)


class ProfileView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

        owners = Customer.objects.filter(user=request.user)
        orders = Order.orders.filter(owner__in=owners).order_by('-created_at')

        categories = Category.objects.all()
        return render(
            request,
            'profile.html',
            {
                'orders': orders,
                'order': self.order,
                'categories': categories,
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
        context['categories'] = Category.objects.all()
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
            'order_placed.html',
            {
                'site_url': settings.SITE_URL,
                'order': pay_order,
            }
        )
