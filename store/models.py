from PIL import Image
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe

User = get_user_model()


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
    MAX_DIMENSIONS = (3000, 3000)
    MAX_IMAGE_SIZE = 3145728

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
    price_discount = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена со скидкой', null=True, blank=True)
    length = models.IntegerField(verbose_name='Длина, см', null=True, blank=True)
    width = models.IntegerField(verbose_name='Ширина, см', null=True, blank=True)
    height = models.IntegerField(verbose_name='Высота, см', null=True, blank=True)
    weight = models.IntegerField(verbose_name='Вес, гр', null=True, blank=True)
    material = models.CharField(verbose_name='Материал', max_length=20, null=True, blank=True)
    color = models.CharField(verbose_name='Цвет', max_length=20, null=True, blank=True)
    bestseller = models.BooleanField(verbose_name='Хит', default=False)
    new = models.BooleanField(verbose_name='Новинка', default=False)
    gift = models.BooleanField(verbose_name='Подарок', blank=False, null=False, default=False)
    gender = models.CharField(verbose_name='Пол', max_length=1, blank=False, null=False, default='G', choices=GENDER_CHOICES)
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
        return mark_safe('<img src="/media/%s" width="50" height="50" />' % self.image)

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
        return mark_safe('<img src="/media/%s" width="50" height="50" />' % self.image)

    image_tag.short_description = 'Изображение'


class Customer(models.Model):

    class Meta:
        verbose_name = 'Сессия'
        verbose_name_plural = '[ Сессии ]'

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Адрес', null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name='Заказы клиента', related_name='related_order')
    session = models.CharField(max_length=200, null=True, blank=True, verbose_name='Сессия клиента')
    created = models.DateTimeField(auto_now=True, verbose_name='Дата подключения клиента')

    def __str__(self):
        if self.user:
            name = "{} {}".format(self.user.first_name, self.user.last_name)
        else:
            name = f"Аноним {self.session[0:5]}..."
        return name


class OrderProduct(models.Model):

    class Meta:
        verbose_name = 'Товар заказа'
        verbose_name_plural = 'Товары заказа'

    order = models.ForeignKey('Order', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products')
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1, verbose_name='шт')
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')

    def __str__(self):
        return self.product.title

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.product.price
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
    STATUS_PAID = 'paid'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_RECEIVED = 'received'
    STATUS_CANCELED = 'canceled'
    STATUS_RETURN = 'return'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY1 = 'delivery1'
    BUYING_TYPE_DELIVERY2 = 'delivery2'

    STATUS_CHOICES = (
        (STATUS_CART, 'Корзина'),
        (STATUS_NEW, 'Оформлен'),
        (STATUS_PAID, 'Оплачен'),
        (STATUS_IN_PROGRESS, 'В обработке'),
        (STATUS_READY, 'Готов'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_DELIVERED, 'Доставлен в место выдачи'),
        (STATUS_RECEIVED, 'Получен'),
        (STATUS_RETURN, 'Возврат'),
        (STATUS_CANCELED, 'Отменен'),
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз из торгового центра'),
        (BUYING_TYPE_DELIVERY1, 'Доставка в пункт выдачи'),
        (BUYING_TYPE_DELIVERY2, 'Почтовая доставка'),
    )

    # user = models.ForeignKey(User, verbose_name='Автор', related_name='related_orders', on_delete=models.CASCADE)
    owner = models.ForeignKey(Customer, null=True, verbose_name='Покупатель', on_delete=models.CASCADE)
    products = models.ManyToManyField(OrderProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(verbose_name='Товары', default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая сумма')

    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон', null=True, blank=True)
    postal_code = models.CharField(max_length=30, verbose_name='Индекс', null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказа',
        choices=STATUS_CHOICES,
        default=STATUS_CART
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=BUYING_TYPE_CHOICES,
        null=True,
        default=None
    )
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    remark = models.CharField(max_length=255, verbose_name='Примечания от магазина',
                              null=True, blank=True, help_text='Служебные примечания, клиенту недоступны')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата заказа')
    is_paid = models.BooleanField(default=False)  # оплачен ли заказ
    shipped_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return \
            'Заказ: {}. {} {} {}'.format(
                str(self.id), self.last_name, self.first_name, self.phone
            )
