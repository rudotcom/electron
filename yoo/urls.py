from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from yoo.views import YooStatusView


urlpatterns = [
    path('', csrf_exempt(YooStatusView.as_view()), name='yoo_status'),
]