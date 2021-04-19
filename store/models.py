import os
from uuid import uuid4

import telepot
from PIL import Image
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe

from Introvert import settings
from store.utils import path_and_rename


class Parameter(models.Model):
    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        ordering = ('name',)

    value = models.IntegerField(verbose_name='Значение')
    name = models.CharField(max_length=255, verbose_name='Имя')
    meaning = models.TextField(verbose_name='Описание', null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        parameter[self.name] = int(self.value)
        super().save(*args, **kwargs)


class MinDimentionErrorException(Exception):
    pass


class Category(models.Model):
    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ('id',)

    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class SubCategoryManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()

    def get_subcategory_list(self):
        # models = get_model_counter('shopperbag', 'waistbag', 'backpack', 'accessory')
        # models = get_model_counter(category)
        q = self.get_queryset().annotate()
        data = [
            dict(name=c.name, url=c.get_absolute_url()) for c in q
        ]
        return data


class SubCategory(models.Model):
    class Meta:
        verbose_name = 'Подгруппа'
        verbose_name_plural = 'Подгруппы'
        ordering = ('category', 'name')

    name = models.CharField(max_length=255, verbose_name='Подгруппа')
    category = models.ForeignKey(Category, verbose_name='Группа', null=False, blank=False, default=1,
                                 on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)
    objects = SubCategoryManager()
    count = models.IntegerField(null=True)

    def __str__(self):
        return "{} {}".format(self.category, self.name)

    def get_absolute_url(self):
        return reverse('subcategory_detail', kwargs={'slug': self.slug})


class RandomManager(models.Manager):
    def get_query_set(self):
        return super(RandomManager, self).get_query_set().order_by('?')


class Product(models.Model):
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = '2. Товары'
        ordering = ('subcategory', 'title')

    PRODUCT_BIG = (1100, 3000)
    PRODUCT_CARD = (300, 400)
    PRODUCT_THUMB = (50, 50)
    MAX_IMAGE_SIZE = 4145728

    GENDER_CHOICES = (
        ('G', 'Для всех'),
        ('M', 'Для мужчин'),
        ('F', 'Для женщин'),
    )

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, verbose_name='Подгруппа', null=False, blank=False, default=1,
                                    on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение', upload_to=path_and_rename)
    description = models.TextField(verbose_name='Описание', null=True)
    care = models.TextField(verbose_name='Инструкция по уходу', null=True, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')
    price_discount = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена со скидкой',
                                         null=True, blank=True)
    length = models.IntegerField(verbose_name='Длина, см', null=True, blank=True)
    width = models.IntegerField(verbose_name='Ширина, см', null=True, blank=True)
    height = models.IntegerField(verbose_name='Высота, см', null=True, blank=True)
    weight = models.IntegerField(verbose_name='Вес, гр', null=True, blank=True)
    material = models.CharField(verbose_name='Материал', max_length=20, null=True, blank=True)
    color = models.CharField(verbose_name='Цвет', max_length=20, null=True, blank=True)
    bestseller = models.BooleanField(verbose_name='Хит', default=False)
    new = models.BooleanField(verbose_name='Новинка', default=False)
    gift = models.BooleanField(verbose_name='Подарок', blank=False, null=False, default=False)
    gender = models.CharField(verbose_name='Пол', max_length=1, blank=False, null=False, default='G',
                              choices=GENDER_CHOICES)
    quantity = models.PositiveIntegerField(verbose_name='Наличие', default=0)
    display = models.BooleanField(verbose_name='Выставлять', default=True,
                                  blank=False, null=False)
    limited = models.BooleanField(verbose_name='Лимитированный выпуск', default=False, blank=False, null=False)
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    visits = models.IntegerField(default=0, verbose_name='👁', help_text='Количество просмотров')
    last_visit = models.DateTimeField(blank=True, null=True, verbose_name='Просмотрен')
    objects = models.Manager()  # The default manager.
    randoms = RandomManager()  # The random-specific manager.

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        min_width, min_height = self.PRODUCT_CARD

        if img.height < min_height or img.width < min_width:
            raise MinDimentionErrorException('Загруженное изображение меньше допустимого {}x{}'.format(
                *self.PRODUCT_CARD))
        else:
            ext = image.name.split('.')[-1]
            filename = f'{self.category.slug}_{self.slug}.{ext}'

            img.thumbnail(self.PRODUCT_BIG, Image.ANTIALIAS)
            img.save(os.path.join(settings.MEDIA_ROOT, filename), 'JPEG', quality=95)

            img.thumbnail(self.PRODUCT_CARD, Image.ANTIALIAS)
            img.save(os.path.join(settings.MEDIA_ROOT, 'card', filename), 'JPEG', quality=85)

            img.thumbnail(self.PRODUCT_THUMB)
            img.save(os.path.join(settings.MEDIA_ROOT, 'thumb', filename))

        super().save(*args, **kwargs)

    def image_thumb(self):
        return mark_safe('<img src="/media/thumb/%s">' % self.image)

    image_thumb.short_description = 'Изображение'


class ProductImage(models.Model):
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товара'

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField()

    def __str__(self):
        return self.product.title

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)

        ext = image.name.split('.')[-1]
        filename = '{}.{}'.format(uuid4().hex, ext)
        image.name = filename
        super().save(*args, **kwargs)
        os.remove(os.path.join(settings.MEDIA_ROOT, filename))

        img.thumbnail(Product.PRODUCT_BIG, Image.ANTIALIAS)
        img.save(os.path.join(settings.MEDIA_ROOT, filename), 'JPEG', quality=85)

        img.thumbnail(Product.PRODUCT_CARD, Image.ANTIALIAS)
        img.save(os.path.join(settings.MEDIA_ROOT, 'card', filename), 'JPEG', quality=85)

        img.thumbnail(Product.PRODUCT_THUMB)
        img.save(os.path.join(settings.MEDIA_ROOT, 'thumb', filename))

    def image_thumb(self):
        return mark_safe('<img src="/media/thumb/%s" height="50" />' % self.image)

    image_thumb.short_description = 'Изображение'


class Customer(models.Model):
    class Meta:
        verbose_name = 'Сессия'
        verbose_name_plural = '[ Сессии ]'

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    orders = models.ManyToManyField('Order', verbose_name='Заказы клиента', related_name='related_order')
    session = models.CharField(max_length=200, null=True, blank=True, verbose_name='Сессия клиента')
    created = models.DateTimeField(auto_now=True, verbose_name='Дата подключения клиента')

    def __str__(self):
        if self.user:
            name = f'{self.user.username} [ {self.user.email} ]'
        else:
            name = f"Аноним {self.session[0:5]}..."
        return name


class OrderProduct(models.Model):
    class Meta:
        verbose_name = 'Товар заказа'
        verbose_name_plural = 'Товары заказа'

    order = models.ForeignKey('Order', verbose_name='Корзина', on_delete=models.CASCADE,
                              related_name='related_products')
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1, verbose_name='шт')
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')

    def __str__(self):
        return self.product.title

    def save(self, *args, **kwargs):
        price = self.product.price_discount if self.product.price_discount else self.product.price
        self.final_price = self.qty * price
        super().save(*args, **kwargs)

    def image_thumb(self):
        return mark_safe('<img src="/media/thumb/%s" width="50" height="50" />' % self.product.image)

    image_thumb.short_description = 'Изображение'


class ActiveOrderManager(models.Manager):
    def get_queryset(self):
        return super(ActiveOrderManager, self).get_queryset().exclude(status='cart')


class CartManager(models.Manager):
    def get_queryset(self):
        return super(CartManager, self).get_queryset().filter(status='cart')


class Order(models.Model):
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = '1. Заказы'

    STATUS_CART = 'cart'
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_RECEIVED = 'received'
    STATUS_CANCELED = 'canceled'
    STATUS_RETURN = 'return'

    DELIVERY_TYPE_SELF = 'self'
    DELIVERY_TYPE_CDEKSPB = 'delivery_cdekspb'
    DELIVERY_TYPE_SPB = 'delivery_spb'
    DELIVERY_TYPE_RU = 'delivery_ru'
    DELIVERY_TYPE_WORLD = 'delivery_world'

    PAYMENT_TYPE0 = 'cash_card'
    PAYMENT_TYPE1 = 'bankcard'
    PAYMENT_TYPE2 = 'wallet'

    STATUS_CHOICES = (
        (STATUS_CART, 'Корзина'),
        (STATUS_NEW, 'Оформлен'),
        (STATUS_IN_PROGRESS, 'В обработке'),
        (STATUS_READY, 'Готов'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_DELIVERED, 'Доставлен в место выдачи'),
        (STATUS_RECEIVED, 'Получен'),
        (STATUS_RETURN, 'Возврат'),
        (STATUS_CANCELED, 'Отменен'),
    )

    DELIVERY_TYPE_CHOICES = (
        (DELIVERY_TYPE_SELF, 'Самовывоз из мастерской (бесплатно)'),
        (DELIVERY_TYPE_CDEKSPB, 'Доставка до пункта выдачи СДЭК по СПб'),
        (DELIVERY_TYPE_SPB, 'Курьерская доставка по СПб'),
        (DELIVERY_TYPE_RU, 'Почтовая отправка по России'),
        (DELIVERY_TYPE_WORLD, 'Почтовая отправка за рубеж'),
    )

    PAYMENT_CHOICES = (
        (PAYMENT_TYPE0, 'Наличные или банковская карта в мастерской'),
        (PAYMENT_TYPE1, 'Банковская карта онлайн'),
        (PAYMENT_TYPE2, 'Kiwi кошелёк / Paypal'),
    )

    # user = models.ForeignKey(User, verbose_name='Автор', related_name='related_orders', on_delete=models.CASCADE)
    owner = models.ForeignKey(Customer, null=True, verbose_name='Покупатель', on_delete=models.CASCADE)
    products = models.ManyToManyField(OrderProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(verbose_name='Товары', default=0)
    total_price_net = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Сумма товаров')
    total_price_gross = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая сумма')
    gift = models.ForeignKey(Product, null=True, verbose_name='Подарок', on_delete=models.DO_NOTHING)
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказа',
        choices=STATUS_CHOICES,
        default=STATUS_CART
    )
    delivery_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=DELIVERY_TYPE_CHOICES,
        null=True,
        default=None
    )
    delivery_cost = models.DecimalField(max_digits=9, decimal_places=2, default=0, verbose_name='Стоимость доставки')
    payment_type = models.CharField(
        max_length=100,
        verbose_name='Способ оплаты',
        choices=PAYMENT_CHOICES,
        null=True,
        default=None,
    )
    payment_id = models.CharField(max_length=50, null=True, default=None, verbose_name='id платежа в Юkassa')
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    remark = models.CharField(max_length=255, verbose_name='Примечания от магазина',
                              null=True, blank=True, help_text='Служебные примечания, клиенту недоступны')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата заказа')
    is_paid = models.BooleanField(default=False, verbose_name='Оплачен')  # оплачен ли заказ
    shipped_date = models.DateTimeField(blank=True, null=True)
    tracking = models.CharField(max_length=50, verbose_name='Трекинг номер', null=True, blank=True)

    first_name = models.CharField(max_length=50, verbose_name='Имя', blank=True)
    last_name = models.CharField(max_length=50, verbose_name='Фамилия', blank=True)
    patronymic = models.CharField(max_length=50, verbose_name='Отчество', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон', blank=True)
    settlement = models.CharField(max_length=100, verbose_name='Населенный пункт', blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адрес', blank=True)
    postal_code = models.CharField(max_length=30, verbose_name='Индекс', blank=True)
    orders = ActiveOrderManager()
    carts = CartManager()

    def __str__(self):
        return \
            'Заказ: {}. {} {} {}'.format(
                str(self.id), self.last_name, self.first_name, self.phone
            )

    def get_fio(self):
        return f'{self.last_name} {self.first_name[0:1]}.{self.patronymic[0:1]}'

    get_fio.short_description = 'Ф.И.О.'

    def save(self, *args, **kwargs):
        free_gift = get_parameter('FREE_GIFT')
        free_delivery = get_parameter('FREE_DELIVERY')

        # Если сумма меньше бонусной, удалить подарок
        if self.total_price_net < free_gift:
            self.gift = None

        # Пересчитать стоимость доставки
        if self.delivery_type == self.DELIVERY_TYPE_SELF:
            self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_SPB:  # spb
            if self.total_price_net < free_delivery:
                delivery_courier_cost = int(Parameter.objects.get(name='DELIVERY_COURIER_COST').value)
                self.delivery_cost = delivery_courier_cost
            else:
                self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_CDEKSPB:  # CDEK spb
            if self.total_price_net < free_delivery:
                delivery_cdek_cost = int(Parameter.objects.get(name='DELIVERY_CDEK_COST').value)
                self.delivery_cost = delivery_cdek_cost
            else:
                self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_RU:  # RU
            if self.total_price_net < free_delivery:
                delivery_ru_cost = int(Parameter.objects.get(name='DELIVERY_RU_COST').value)
                self.delivery_cost = delivery_ru_cost
            else:
                self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_WORLD:  # World
            delivery_world_cost = int(Parameter.objects.get(name='DELIVERY_WORLD_COST').value)
            self.delivery_cost = delivery_world_cost

        # Пересчитать сумму в корзине
        if self.id and self.products.count():
            cart_data = self.products.aggregate(models.Sum('final_price'), models.Count('id'))
            self.total_price_net = cart_data.get('final_price__sum')
            self.total_products = cart_data['id__count']
            self.total_price_gross = self.total_price_net + self.delivery_cost
        else:
            self.total_price_net = 0
            self.total_price_gross = 0
            self.total_products = 0
            self.delivery_type = None
            self.delivery_cost = 0

        super().save(*args, **kwargs)

    @staticmethod
    def send_telegram(text):
        group_id = get_parameter('TELEGRAM_GROUP')
        telegram_token = os.getenv('telegram_token')
        telegram_bot = telepot.Bot(telegram_token)  # token
        telegram_bot.sendMessage(group_id, text, parse_mode="Markdown")


class Article(models.Model):
    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'
        ordering = ('id',)

    title = models.CharField(max_length=255, verbose_name='Заголовок')
    name = models.CharField(max_length=50, verbose_name='Пункт меню', null=False, blank=False)
    slug = models.SlugField(unique=True, null=False)
    content = models.TextField(verbose_name='Текст страницы', null=True)

    def get_absolute_url(self):
        return reverse('article', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


def get_parameter(name):
    return int(Parameter.objects.get(name=name).value)


parameter = {
    'FREE_GIFT': get_parameter('FREE_GIFT'),
    'FREE_DELIVERY': get_parameter('FREE_DELIVERY'),
    'DELIVERY_COURIER_COST': get_parameter('DELIVERY_COURIER_COST'),
    'DELIVERY_CDEK_COST': get_parameter('DELIVERY_CDEK_COST'),
    'DELIVERY_RU_COST': get_parameter('DELIVERY_RU_COST'),
    'DELIVERY_WORLD_COST': get_parameter('DELIVERY_WORLD_COST'),
}
