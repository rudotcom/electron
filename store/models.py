from PIL import Image
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe

User = get_user_model()
FREE_DELIVERY = 2500  # Сумма, при которой доставка по РФ бесплатна
FREE_GIFT = 800  # Сумма, при которой добавляется возможность выбрать подарок
DELIVERY_CDEK_COST = 300  # Доставка до ближайшего к Вам пункта выдачи СДЭК (по СПб)
DELIVERY_COURIER_COST = 450  # Доставка заказа курьером лично в руки, по городу Санкт-Петербургу
DELIVERY_RU_COST = 300  # В любой другой город России, доставка посредством почты, стоимость доставки 300₽
DELIVERY_WORLD_COST = 900  # Стоимость доставки заказа авиа почтой по миру: 900₽.


class MinDimentionErrorException(Exception):
    pass


class MaxDimentionErrorException(Exception):
    pass


class Category(models.Model):

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = '[ Группы ]'
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
        verbose_name_plural = '[ Подгруппы ]'
        ordering = ('category', 'name')

    name = models.CharField(max_length=255, verbose_name='Подгруппа')
    category = models.ForeignKey(Category, verbose_name='Группа', null=False, blank=False, default=1,
                                 on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)
    objects = SubCategoryManager()

    def __str__(self):
        return "{} {}".format(self.category, self.name)

    def get_absolute_url(self):
        return reverse('subcategory_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = '[ 2. Товары ]'
        ordering = ('subcategory', 'title')

    MIN_DIMENSIONS = (400, 400)
    MAX_DIMENSIONS = (4500, 4500)
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
    image = models.ImageField(verbose_name='Изображение')
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

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        min_width, min_height = self.MIN_DIMENSIONS
        max_width, max_height = self.MAX_DIMENSIONS

        if img.height < min_height or img.width < min_width:
            raise MinDimentionErrorException('Загруженное изображение меньше допустимого {}x{}'.format(
                *self.MIN_DIMENSIONS))
        if img.height > max_height or img.width > max_width:
            raise MaxDimentionErrorException('Загруженное изображение больше допустимого {}x{}'.format(
                *self.MAX_DIMENSIONS))
        super().save(*args, **kwargs)

    def image_tag(self):
        return mark_safe('<img src="/media/%s" height="50" />' % self.image)

    image_tag.short_description = 'Изображение'


class ProductImage(models.Model):

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товара'

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField()

    def __str__(self):
        return self.product.title

    def image_tag(self):
        return mark_safe('<img src="/media/%s" height="50" />' % self.image)

    image_tag.short_description = 'Изображение'


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

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" />' % self.product.image)

    image_tag.short_description = 'Изображение'


class Order(models.Model):

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = '[ 1. Заказы ]'

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
    PAYMENT_TYPE2 = 'kiwi'

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
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая сумма')
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
        default=None
    )
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

    def __str__(self):
        return \
            'Заказ: {}. {} {} {}'.format(
                str(self.id), self.last_name, self.first_name, self.phone
            )

    def get_fio(self):
        return f'{self.last_name} {self.first_name[0:1]}.{self.patronymic[0:1]}'
    get_fio.short_description = 'Ф.И.О.'

    def save(self, *args, **kwargs):
        # Пересчитать сумму в корзине
        if self.id:
            cart_data = self.products.aggregate(models.Sum('final_price'), models.Count('id'))
            if cart_data.get('final_price__sum'):
                self.final_price = cart_data['final_price__sum'] + self.delivery_cost
            else:
                self.final_price = 0
            self.total_products = cart_data['id__count']
        else:
            self.final_price = 0
            self.total_products = 0

        """
        Если сумма меньше бонусной, удалить подарок
        Если больше и подарка в корзине нет, перенести подарок из корзины в ячейку order.gift
        """
        if self.final_price < FREE_GIFT:
            self.gift = None
        # elif not self.gift:
        #     # Найти товар в корзине, уменьшить количество на 1 и создать подарок в заказе
        #     for order_product in self.products.all():
        #         if order_product.product.gift:
        #             qty = order_product.qty
        #             if qty > 1:
        #                 order_product.qty -= 1
        #                 order_product.save()
        #             else:
        #                 self.products.remove(order_product)
        #                 order_product.delete()
        #             self.gift = order_product.product
        #             break

        # Пересчитать стоимость доставки в зависимости от суммы корзины
        if self.delivery_type == self.DELIVERY_TYPE_SELF:
            self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_SPB:  # spb
            if self.final_price < FREE_DELIVERY:
                self.delivery_cost = DELIVERY_COURIER_COST
            else:
                self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_CDEKSPB:  # CDEK spb
            if self.final_price < FREE_DELIVERY:
                self.delivery_cost = DELIVERY_CDEK_COST
            else:
                self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_RU:  # RU
            if self.final_price < FREE_DELIVERY:
                self.delivery_cost = DELIVERY_RU_COST
            else:
                self.delivery_cost = 0
        elif self.delivery_type == self.DELIVERY_TYPE_WORLD:  # World
            self.delivery_cost = DELIVERY_WORLD_COST

        super().save(*args, **kwargs)
