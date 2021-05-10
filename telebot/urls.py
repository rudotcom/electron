from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from telebot.views import TgView


urlpatterns = [
    path('', csrf_exempt(TgView.as_view()), name='tg'),
]