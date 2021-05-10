import os

from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import View
import json
import requests
from store.models import Product


class TgView(View):
    """
    Telegram web hook view
    """
    model = Product
    TELEGRAM_URL = "https://api.telegram.org/bot"
    TELEGRAM_TOKEN = os.getenv("telegram_token", "error_token")

    def post(self, request, *args, **kwargs):
        print(request.body)
        t_data = json.loads(request.body)
        t_message = t_data["message"]
        t_chat = t_message["chat"]

        try:
            query = t_message["text"].strip().lower()
        except Exception as e:
            return JsonResponse({"ok": "POST request processed"})

        object_list = Product.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        found = object_list.count()
        found_text = f'Найдено товаров {found} ({query}):' if found else f'Таких товаров не найдено: {query}'
        self.send_message(t_chat['id'], found_text)

        i = 0
        for item in object_list:
            i += 1
            msg = render_to_string('telebot/product_card.html', {
                'i': i,
                'qty': item.quantity,
                'price': item.price,
                'title': item.title,
                'slug': item.slug,
            })
            self.send_photo(chat_id=t_chat["id"], photo=item.image.name, caption=msg)

        return JsonResponse({"ok": "POST request processed"})

    def send_message(self, chat_id, message):
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "MarkdownV2",
        }
        response = requests.post(
            f"{self.TELEGRAM_URL}{self.TELEGRAM_TOKEN}/sendMessage",
            data=data
        )

    def send_photo(self, photo, caption, chat_id):
        url = 'introvert.com.ru'

        data = {
            'photo': f'https://{url}/media/card/{photo}',
            "chat_id": chat_id,
            "caption": caption.replace('.', '\.').replace('-', '\-').replace('&quot;', '"'),
            "parse_mode": "MarkdownV2",
        }

        response = requests.post(
            f"{self.TELEGRAM_URL}{self.TELEGRAM_TOKEN}/sendPhoto",
            data=data
        )
