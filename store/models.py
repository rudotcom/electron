import os
from PIL import Image
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe

from electron import settings
from store.utils import path_and_rename

NO_IMAGE_URL = '/static/img/no_image.png'
NO_IMAGE_THUMB = '/static/img/no_image_thumb.png'


class Group(models.Model):
    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ('id',)

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Группа')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('group_detail', kwargs={'pk': self.pk})


class CategoryManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()

    def get_category_list(self):
        q = self.get_queryset().annotate()
        data = [
            dict(name=c.name, url=c.get_absolute_url()) for c in q
        ]
        return data


class Category(models.Model):
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('parent', 'name')

    id = models.IntegerField(primary_key=True)
    parent = models.ForeignKey(Group, verbose_name='Группа', null=False,
                               blank=False, default=1,
                               on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Категория')
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'pk': self.pk})


class Product(models.Model):
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = '2. Товары'
        ordering = ('category', 'title')

    PRODUCT_BIG = (1100, 3000)
    PRODUCT_CARD = (300, 400)
    PRODUCT_THUMB = (50, 50)
    MAX_IMAGE_SIZE = 4145728

    category = models.ForeignKey(Category, verbose_name='Категория',
                                 null=False, blank=False, default=1,
                                 on_delete=models.CASCADE)
    article = models.CharField(max_length=50, verbose_name='Артикул')
    title = models.CharField(max_length=255, verbose_name='Наименование')
    image = models.ImageField(verbose_name='Изображение', blank=True,
                              null=True, upload_to=path_and_rename)
    price = models.DecimalField(max_digits=9, decimal_places=2,
                                verbose_name='Цена', default=0)
    warehouse1 = models.PositiveIntegerField(verbose_name='Склад ЭЛЕКТРОН', default=0)
    warehouse2 = models.PositiveIntegerField(verbose_name='Склад ЭЛЕКТРИКА', default=0)
    display = models.BooleanField(verbose_name='Выставлять', default=True,
                                  blank=False, null=False)

    def __str__(self):
        return self.title

    @property
    def quantity(self):
        return sum([self.warehouse1, self.warehouse2])

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        image = self.image
        if image:
            img = Image.open(image)

            ext = image.name.split('.')[-1]
            filename = f'{self.category.pk}_{self.pk}.{ext}'

            img.thumbnail(self.PRODUCT_BIG, Image.ANTIALIAS)
            img.save(os.path.join(settings.MEDIA_ROOT, filename),
                     'JPEG', quality=95)

            img.thumbnail(self.PRODUCT_CARD, Image.ANTIALIAS)
            img.save(os.path.join(settings.MEDIA_ROOT, 'card', filename),
                     'JPEG', quality=85)

            img.thumbnail(self.PRODUCT_THUMB)
            img.save(os.path.join(settings.MEDIA_ROOT, 'thumb', filename))

        super().save(*args, **kwargs)

    def image_thumb(self):
        img_src = f"/media/thumb/{self.image}" if self.image else NO_IMAGE_THUMB
        return mark_safe(
            f'<img src="{img_src}" width="50" height="50" />'
        )

    image_thumb.short_description = 'Изображение'

    def image_name(self):
        return f"/media/card/{self.image}" if self.image else NO_IMAGE_URL


class Customer(models.Model):
    user = models.ForeignKey(User, null=True, blank=True,
                             on_delete=models.CASCADE)
    orders = models.ManyToManyField('Order', verbose_name='Заказы клиента',
                                    related_name='related_order')
    session = models.CharField(max_length=200, null=True,
                               blank=True, verbose_name='Сессия клиента')
    created = models.DateTimeField(auto_now=True,
                                   verbose_name='Дата подключения клиента')
    code = models.CharField(max_length=200, null=True, blank=True,
                            verbose_name='Код подтверждения email')
    confirmed = models.BooleanField(default=False, verbose_name='email подтвержден')
    first_name = models.CharField(max_length=50, verbose_name='Имя',
                                  blank=True)
    last_name = models.CharField(max_length=50, verbose_name='Фамилия',
                                 blank=True)
    patronymic = models.CharField(max_length=50, verbose_name='Отчество',
                                  blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон',
                             blank=True)

    def __str__(self):
        if self.user:
            name = f'{self.user.username} [ {self.user.email} ]'
        else:
            name = f"Аноним {self.session[0:5]}..."
        return name


class OrderProduct(models.Model):
    order = models.ForeignKey('Order', verbose_name='Корзина',
                              on_delete=models.CASCADE,
                              related_name='related_products')
    product = models.ForeignKey(Product, verbose_name='Товар',
                                on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1, verbose_name='шт')
    final_price = models.DecimalField(max_digits=9, decimal_places=2,
                                      verbose_name='Общая цена')

    def __str__(self):
        return self.product.title

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.product.price
        super().save(*args, **kwargs)

    def image_thumb(self):
        img_src = f"/media/thumb/{self.product.image}" if self.product.image else NO_IMAGE_THUMB
        return mark_safe(
            f'<img src="{img_src}" width="50" height="50" />'
        )

    image_thumb.short_description = 'Изображение'


class ActiveOrderManager(models.Manager):
    def get_queryset(self):
        return super(ActiveOrderManager, self).get_queryset(). \
            exclude(status='cart')


class CartManager(models.Manager):
    def get_queryset(self):
        return super(CartManager, self).get_queryset().filter(status='cart')


class Order(models.Model):
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = '1. Заказы'

    STATUS_CART = 'cart'
    STATUS_NEW = 'new'
    STATUS_APPROVED = 'approved'
    STATUS_PROCESSED = 'processed'
    STATUS_READY = 'is_ready'
    STATUS_FINISHED = 'finished'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = (
        (STATUS_CART, 'Корзина'),
        (STATUS_NEW, 'Оформлен клиентом'),
        (STATUS_APPROVED, 'Подтвержден'),
        (STATUS_PROCESSED, 'Обработан'),
        (STATUS_READY, 'Готов к выдаче'),
        (STATUS_FINISHED, 'Завершен'),
        (STATUS_CANCELED, 'Отменен'),
    )

    owner = models.ForeignKey(
        Customer, null=True, verbose_name='Покупатель',
        on_delete=models.CASCADE
    )
    products = models.ManyToManyField(OrderProduct, blank=True,
                                      related_name='related_cart')
    total_products = models.PositiveIntegerField(verbose_name='Товары',
                                                 default=0)
    total_price_net = models.DecimalField(
        max_digits=9, default=0,
        decimal_places=2, verbose_name='Сумма товаров'
    )
    total_price_gross = models.DecimalField(
        max_digits=9, default=0,
        decimal_places=2,
        verbose_name='Общая сумма'
    )
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказа',
        choices=STATUS_CHOICES,
        default=STATUS_CART
    )
    comment = models.TextField(verbose_name='Комментарий к заказу',
                               null=True, blank=True)
    remark = models.CharField(
        max_length=255, verbose_name='Примечания от магазина',
        null=True, blank=True,
        help_text='Служебные примечания, клиенту недоступны'
    )
    created_at = models.DateTimeField(default=timezone.now,
                                      verbose_name='Дата заказа')
    first_name = models.CharField(max_length=50, verbose_name='Имя',
                                  blank=True)
    last_name = models.CharField(max_length=50, verbose_name='Фамилия',
                                 blank=True)
    patronymic = models.CharField(max_length=50, verbose_name='Отчество',
                                  blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон',
                             blank=True)
    orders = ActiveOrderManager()
    carts = CartManager()

    def __str__(self):
        return \
            'Заказ: {}. {} {} {}'.format(
                str(self.id), self.last_name, self.first_name, self.phone
            )

    def get_fio(self):
        return f'{self.last_name} {self.first_name[0:1]}.' \
               f'{self.patronymic[0:1]}'

    get_fio.short_description = 'Ф.И.О.'

    def save(self, *args, **kwargs):

        # Пересчитать сумму в корзине
        if self.id and self.products.count():
            cart_data = self.products.aggregate(
                models.Sum('final_price'), models.Count('id')
            )
            self.total_price_net = cart_data.get('final_price__sum')
            self.total_products = cart_data['id__count']
        else:
            self.total_price_net = 0
            self.total_price_gross = 0
            self.total_products = 0
            self.delivery_type = None
            self.delivery_cost = 0

        super().save(*args, **kwargs)


class Article(models.Model):
    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'
        ordering = ('id',)

    title = models.CharField(max_length=255, verbose_name='Заголовок')
    name = models.CharField(max_length=50, verbose_name='Пункт меню',
                            null=False, blank=False)
    slug = models.SlugField(unique=True, null=False)
    content = models.TextField(verbose_name='Текст страницы', null=True)

    def get_absolute_url(self):
        return reverse('article', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title
