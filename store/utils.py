import os
import random
import string
from electron.settings import MEDIA_ROOT
import pymorphy2

morph = pymorphy2.MorphAnalyzer()


def path_and_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{instance.category.pk}_{instance.pk}.{ext}'
    os.remove(os.path.join(MEDIA_ROOT, filename))
    return f'{filename}'


def get_random_session():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=36))
