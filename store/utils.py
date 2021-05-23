import os
import random
import string

from Introvert.settings import MEDIA_ROOT
import pymorphy2
morph = pymorphy2.MorphAnalyzer()


def path_and_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{instance.category.slug}_{instance.slug}.{ext}'
    os.remove(os.path.join(MEDIA_ROOT, filename))
    return f'{filename}'


def reconcile_verb_gender(verb, item):
    """согласование рода глагола "добавлен", "удален" с наименованием товара
    """
    phrase = item.split(' ')
    word = phrase[0]
    tag = str(morph.parse(word)[0].tag)
    for form in morph.parse(word):
        if 'nomn' in form.tag:
            tag = form.tag
            break

    if 'plur' in tag:
        return f'{verb}ы'
    if 'masc' in tag:
        return f'{verb}'
    elif 'femn' in tag:
        return f'{verb}a'
    else:
        return f'{verb}о'


def get_random_session():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=56))
