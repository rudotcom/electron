from django.db.models.signals import post_save
from django.dispatch import receiver

from store.models import Product, SubCategory


@receiver(post_save, sender=Product)
def count_subcategory_items(sender, instance, **kwargs):
    print('sender:', sender)
    print('instance:', instance)
    subcategory = SubCategory.objects.get(id=instance.subcategory.id)
    subcategory.count = subcategory.objects.count()
    subcategory.save()
