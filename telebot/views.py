import os
from django.http import JsonResponse
from django.views.generic import View
import json
import requests


# https://api.telegram.org/bot<token>/setWebhook?url=<url>/tg/
class TgView(View):
    """
    Telegram web hook view
    """
    TELEGRAM_URL = "https://api.telegram.org/bot"
    TELEGRAM_TOKEN = os.getenv("telegram_token", "error_token")

    def post(self, request, *args, **kwargs):
        t_data = json.loads(request.body)
        t_message = t_data["message"]
        t_chat = t_message["chat"]

        try:
            text = t_message["text"].strip().lower()
        except Exception as e:
            return JsonResponse({"ok": "POST request processed"})

        msg = text
        self.send_message(msg, t_chat["id"])

        return JsonResponse({"ok": "POST request processed"})

    def send_message(self, message, chat_id):
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        response = requests.post(
            f"{self.TELEGRAM_URL}{self.TELEGRAM_TOKEN}/sendMessage", data=data
        )
