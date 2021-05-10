from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

from store.views import (
    BaseView,
    ProductDetailView,
    CategoryDetailView,
    CartView,
    AddToCartView,
    DeleteFromCartView,
    ChangeQTYView,
    CheckoutView,
    MakeOrderView,
    LoginView,
    RegistrationView,
    ProfileView,
    ProductSearchView,
    SubCategoryDetailView,
    OrderPayView,
    GiftListView,
    ArticleView,

    EmailView, WelcomeView,
)
from yoo.views import BankPaymentView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', WelcomeView.as_view(), name='welcome'),
    path('store/', BaseView.as_view(), name='store'),
    path('about/<str:slug>/', ArticleView.as_view(), name='article'),
    path('search/', ProductSearchView.as_view(), name='search'),
    path('product/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('gifts/', GiftListView.as_view(), name='gifts'),
    path('subcategory/<str:slug>/', SubCategoryDetailView.as_view(), name='subcategory_detail'),
    path('category/<str:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/<str:slug>/', AddToCartView.as_view(), name='add_to_cart'),
    path('remove-from-cart/<str:slug>/', DeleteFromCartView.as_view(), name='delete_from_cart'),
    path('change-qty/<str:slug>/', ChangeQTYView.as_view(), name='change_qty'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('make-order/', MakeOrderView.as_view(), name='make_order'),
    path('order_pay/<int:order>/', OrderPayView.as_view(), name='order_pay'),
    path('order_email/<int:order>/', EmailView.as_view(), name='order_email'),
    path('bank_payment/', BankPaymentView.as_view(), name='bank_payment'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page="/"), name='logout'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('.tg1645429866/', include('telebot.urls')),
    # https://api.telegram.org/bot<token>/setWebhook?url=https://introvert.com.ru/.tg1645429866/
    path('.yoo_status/', include('yoo.urls')),

    path(
        'admin/password_reset/',
        auth_views.PasswordResetView.as_view(),
        name='admin_password_reset',
    ),
    path(
        'admin/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
    path('robots.txt', TemplateView.as_view(template_name="store/robots.txt", content_type="text/plain"),),
]

# nginx сам пересылает /static и /media, эти директивы нужны для tor hidden services
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
