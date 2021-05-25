import git
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
import os
w_secret = os.getenv('w_secret')


def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)


@csrf_exempt
def webhook(request):
    # x_hub_signature = request.headers.get('X-Hub-Signature')
    # if not is_valid_signature(x_hub_signature, request.data, w_secret):
    #     return HttpResponse('Wrong event type', 400)

    if request.method == 'POST':
        repo = git.Repo('/home/rudotcom/ecommerce/.git')
        origin = repo.remotes.origin
        origin.pull()

        return HttpResponse('Updated repo successfully!')
    else:
        return HttpResponse('Wrong event type', 400)
