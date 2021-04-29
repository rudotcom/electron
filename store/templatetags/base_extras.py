from django import template
from store.models import Parameter

register = template.Library()


@register.simple_tag
def parameter(name):
    """
    Получение значения параметра из глобального словаря parameter
    Использование в шаблоне:
    {% load base_extras %}
    {% parameter[<name>] %}
    :param name: str
    :return: str
    """
    return Parameter.objects.get(name=name).value
