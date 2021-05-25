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

from electron import settings
from .forms import LoginForm, RegistrationForm
from .mixins import CartMixin
from .models import Group, Category, Customer, OrderProduct, \
    Product, Order, Article
from .utils import get_random_session


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


class GroupListView(CartMixin, View):
    model = Group

    def get(self, request, *args, **kwargs):
        groups = Group.objects.all()

        context = {
            'groups': groups,
            'order': self.order,
            'articles': self.articles,
        }
        return render(request, 'group_list.html', context)


class ProductDetailView(CartMixin, DetailView):
    model = Product
    template_name = 'item_detail.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['order'] = self.order
        context['articles'] = self.articles

        return context


class CategoryDetailView(CartMixin, DetailView):
    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    template_name = 'category_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = kwargs['object']
        context['order'] = self.order
        context['category_name'] = category.name
        context['category_products'] = category.product_set.all()
        context['articles'] = self.articles
        return context


class GroupDetailView(CartMixin, DetailView):
    model = Group
    queryset = Group.objects.all()
    context_object_name = 'group'
    template_name = 'category_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context['order'] = self.order
        context['group_name'] = group.name
        context['categories'] = Category.objects.filter(
            parent=group
        )
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
            Q(title__icontains=query) | Q(article__icontains=query)
        )
        return object_list


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        session = request.COOKIES.get('customersession') \
                  or get_random_session()

        customer, created = Customer.objects.get_or_create(session=session)
        if request.user.is_authenticated:
            user = User.objects.get(username=request.user)
            customer.user = user
        customer.save()

        self.order, created = Order.carts.get_or_create(owner=customer)
        if created:
            # Это создание новой корзины. Удалить корзины старше 2 дней
            old_carts = Order.carts.filter(
                created_at__lte=datetime.now() - timedelta(days=2)
            )
            old_carts.delete()

        product = Product.objects.get(pk=kwargs['pk'])
        if product.quantity:
            order_product, created = OrderProduct.objects.get_or_create(
                order=self.order, product=product
            )

            if created:
                self.order.products.add(order_product)
                messages.add_message(
                    request,
                    messages.INFO,
                    f'{order_product.product.image_thumb()}'
                    f'Добавлено в корзину: <b>{order_product.product}</b> '
                )
            else:
                if order_product.product.quantity <= order_product.qty:
                    message = f'{order_product.product.image_thumb()}' \
                              f' Количество товара <b>{order_product}</b> ' \
                              f'в корзине {order_product.qty} шт.<br> ' \
                              f'На складе больше нет, извините!'
                    order_product.qty = order_product.product.quantity
                else:
                    order_product.qty += 1
                    message = f'{order_product.product.image_thumb()} ' \
                              f'Количество товара <b>{order_product}</b> ' \
                              f'изменено на {order_product.qty} шт.'

                order_product.save()
                messages.add_message(
                    request,
                    messages.INFO,
                    message
                )
            self.order.save()

        response = HttpResponseRedirect(f"/store/product/{product.pk}/")
        response.set_cookie(key='customersession', value=session)
        return response


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product = Product.objects.get(pk=kwargs['pk'])
        order_product = OrderProduct.objects.get(
            order=self.order, product=product
        )

        self.order.products.remove(order_product)
        order_product.delete()
        self.order.save()
        messages.add_message(request, messages.INFO,
                             f'{order_product.product.image_thumb()} '
                             f' Удалено из корзины: <b>{order_product}</b>')
        return HttpResponseRedirect('/store/cart/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product = Product.objects.get(pk=kwargs['pk'])
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
            message = f'{order_product.product.image_thumb()} ' \
                      f'Количество товара <b>{order_product}</b> ' \
                      f'изменено на {qty} шт.'
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
            messages.add_message(
                request,
                messages.INFO,
                f'{order_product.product.image_thumb()} '
                f'Удалено из корзины: <b>{order_product}</b>'
            )
        self.order.save()
        return HttpResponseRedirect('/store/cart/')


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):

        if not self.order or not self.order.products.count():
            messages.add_message(
                request,
                messages.INFO,
                'Ваша корзина пуста!<br><a href=/store/>'
                'Посмотрите наши товары</a>'
            )

        context = {
            'order': self.order,
            'categories': self.categories,
            'articles': self.articles,
        }
        return render(request, 'cart.html', context)


class CheckoutView(CartMixin, View):

    def post(self, request, *args, **kwargs):

        self.order.delivery_type = request.POST.get('delivery_type')
        self.order.save()

        context = {
            'order': self.order,
            'categories': self.categories,
            'articles': self.articles,
        }

        return render(request, 'checkout.html', context)


class MakeOrderView(LoginRequiredMixin, CartMixin, View):
    login_url = '/login/'

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        user = User.objects.get(username=request.user)
        session = request.COOKIES.get('customersession')

        customer = Customer.objects.get(user=user.id, session=session)
        if not customer.confirmed:
            context = {
                'categories': self.categories,
                'order': self.order,
                'articles': self.articles,
            }
            return render(request, 'registration_confirmation_required.html', context=context)

        order = Order.carts.get(owner=customer)

        order.status = 'new'
        order.save()

        messages.add_message(
            request,
            messages.INFO,
            'Ваш заказ оформлен! \nСпасибо, что выбрали нас. '
            'Как получить заказ......'
        )
        html = render_to_string('email_order_placed.html',
                                {'user': user, 'order': order,
                                 'site_url': settings.SITE_URL})

        send_mail('Заказ в магазине Электр{он/ика}',
                  'Спасибо за Ваш заказ в магазине Электр{он/ика}"!',
                  'Интроверт<noreply@as-electrica.ru>', [user.email],
                  fail_silently=False, html_message=html)

        response = HttpResponseRedirect(f'/order_pay/{order.id}/')
        new_session = get_random_session()
        response.set_cookie(key='customersession', value=new_session)
        return response


class OrderPayView(LoginRequiredMixin, CartMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        user = User.objects.get(username=request.user)

        order_id = kwargs.get('order')

        try:
            # Отображать заказ только если он принадлежит клиенту -
            # текущему пользователю
            order_to_pay = Order.orders.get(id=order_id, owner__user=user)
            show_pay_button = False \
                if order_to_pay.payment_status \
                in ['succeeded', 'waiting_for_capture'] \
                else True

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
        except Exception:
            messages.add_message(
                request, messages.INFO,
                f'Заказа № {order_id} у вас нет! \n'
                f'Выберите свой заказ из списка.'
            )
            return HttpResponseRedirect('/profile/')


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
                session = request.COOKIES.get('customersession') \
                          or get_random_session()
                customer, created = Customer.objects.get_or_create(
                    session=session
                )

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

        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.email = form.cleaned_data['email']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            user = authenticate(
                username=new_user.username,
                password=form.cleaned_data['password']
            )
            login(request, user)
            session = request.COOKIES.get('customersession') \
                or get_random_session()
            customer, created = Customer.objects.get_or_create(session=session)
            customer.code = get_random_session()
            if user:
                customer.user = user
            customer.save()

            # Отправить письмо с кодом подтверждения
            html = render_to_string('email_confirm.html',
                                    {'user': user, 'code': customer.code,
                                     'site_url': settings.SITE_URL})

            send_mail('Подтвердите адрес email',
                      'Подтвердите адрес своей электронной почты!',
                      'Интроверт<noreply@as-electron.ru>', [user.email],
                      fail_silently=False, html_message=html)
            context = {
                'categories': self.categories,
                'order': self.order,
                'articles': self.articles,
            }

            return render(request, 'registration_confirmation_required.html', context=context)

        context = {
            'form': form,
            'categories': self.categories,
            'order': self.order,
            'articles': self.articles,
        }
        return render(request, 'registration.html', context)


class EmailConfirmationView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        context = {
            'categories': self.categories,
            'order': self.order,
            'page_role': 'registration',
            'articles': self.articles,
        }
        code = kwargs.get('code')
        try:
            customer = Customer.objects.get(code=code)
            customer.code = None
            customer.confirmed = True
            customer.save()
            return render(request, 'registration_confirmed.html', context)
        except:
            return render(request, 'registration_confirmation_failed.html', context)



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


class EmailView(LoginRequiredMixin, CartMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        order_id = kwargs.get('order')
        try:
            pay_order = Order.orders.get(id=order_id)

            return render(
                request,
                # 'email_order_placed.html',
                'email_confirm.html',
                {
                    'site_url': settings.SITE_URL,
                    'order': pay_order,
                }
            )
        except Exception:
            return HttpResponse(status=404)
