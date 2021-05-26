from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

from store.views import (
    LoginView,
    RegistrationView,
    ProfileView,
    OrderPayView,
    ArticleView,
    EmailView,
    WelcomeView,
    EmailConfirmationView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', WelcomeView.as_view(), name='welcome'),
    path('', include('store.urls')),
    path('about/<str:slug>/', ArticleView.as_view(), name='article'),
    path('order_pay/<int:order>/', OrderPayView.as_view(), name='order_pay'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page="/"), name='logout'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('confirm/<str:code>', EmailConfirmationView.as_view(), name='email_confirmation'),
    path('profile/', ProfileView.as_view(), name='profile'),

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
    path('gitwebhook/', include('git_hook.urls')),
]

# nginx сам пересылает /static и /media, эти директивы нужны для tor hidden services
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
