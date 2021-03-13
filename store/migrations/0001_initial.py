# Generated by Django 3.1.7 on 2021-03-13 16:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Имя категории')),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'Группа',
                'verbose_name_plural': '[ Группы ]',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Номер телефона')),
                ('address', models.CharField(blank=True, max_length=255, null=True, verbose_name='Адрес')),
                ('session', models.CharField(blank=True, max_length=200, null=True)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='Дата подключения клиента')),
            ],
            options={
                'verbose_name': 'Клиент',
                'verbose_name_plural': '[ Клиенты ]',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_products', models.PositiveIntegerField(default=0, verbose_name='Наименований')),
                ('final_price', models.DecimalField(decimal_places=2, default=0, max_digits=9, verbose_name='Общая цена')),
                ('first_name', models.CharField(max_length=255, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=255, verbose_name='Фамилия')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('postal_code', models.CharField(blank=True, max_length=30, null=True, verbose_name='Индекс')),
                ('address', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Адрес')),
                ('status', models.CharField(choices=[('cart', 'Корзина'), ('new', 'Новый заказ'), ('paid', 'Заказ оплачен'), ('in_progress', 'Заказ в обработке'), ('is_ready', 'Заказ готов'), ('shipped', 'Заказ отправлен'), ('delivered', 'Заказ доставлен в место выдачи'), ('received', 'Заказ получен'), ('completed', 'Заказ завершен'), ('canceled', 'Заказ отменен'), ('return', 'Возврат')], default='cart', max_length=100, verbose_name='Статус заказа')),
                ('buying_type', models.CharField(choices=[('self', 'Самовывоз'), ('delivery1', 'Доставка в пункт выдачи'), ('delivery2', 'Почтовая доставка')], default='self', max_length=100, verbose_name='Тип заказа')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Комментарий к заказу')),
                ('created_at', models.DateTimeField(auto_now=True, verbose_name='Дата создания заказа')),
                ('is_paid', models.BooleanField(default=False)),
                ('shipped_date', models.DateTimeField(blank=True, null=True)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='store.customer', verbose_name='Покупатель')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': '[ 2. Заказы ]',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Наименование')),
                ('slug', models.SlugField(unique=True)),
                ('image', models.ImageField(upload_to='', verbose_name='Изображение')),
                ('description', models.TextField(null=True, verbose_name='Описание')),
                ('care', models.TextField(blank=True, null=True, verbose_name='Инструкция по уходу')),
                ('price', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Цена')),
                ('price_discount', models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name='Цена со скидкой')),
                ('length', models.IntegerField(blank=True, null=True, verbose_name='Длина, см')),
                ('width', models.IntegerField(blank=True, null=True, verbose_name='Ширина, см')),
                ('height', models.IntegerField(blank=True, null=True, verbose_name='Высота, см')),
                ('weight', models.IntegerField(blank=True, null=True, verbose_name='Вес, гр')),
                ('material', models.CharField(blank=True, max_length=20, null=True, verbose_name='Материал')),
                ('color', models.CharField(blank=True, max_length=20, null=True, verbose_name='Цвет')),
                ('bestseller', models.BooleanField(default=False, verbose_name='Хит продаж')),
                ('new', models.BooleanField(default=False, verbose_name='Новинка')),
                ('gift', models.BooleanField(default=False, verbose_name='Подарок')),
                ('gender', models.CharField(blank=True, choices=[('M', 'Для мужчин'), ('F', 'Для женщин'), ('G', 'Для всех')], max_length=1, null=True, verbose_name='Пол')),
                ('quantity', models.PositiveIntegerField(default=0, verbose_name='Наличие')),
                ('display', models.BooleanField(default=True, verbose_name='Выставлять')),
                ('limited', models.BooleanField(default=False, verbose_name='Лимитированный выпуск')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')),
                ('visits', models.IntegerField(default=0, verbose_name='Просмотров')),
                ('last_visit', models.DateTimeField(blank=True, null=True, verbose_name='Просмотрен')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': '[ 1. Товары ]',
                'ordering': ('subcategory', 'title'),
            },
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Подгруппа')),
                ('slug', models.SlugField(unique=True)),
                ('category', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='store.category', verbose_name='Группа')),
            ],
            options={
                'verbose_name': 'Подгруппа',
                'verbose_name_plural': '[ Подгруппы ]',
                'ordering': ('category', 'name'),
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.product')),
            ],
            options={
                'verbose_name': 'Изображение',
                'verbose_name_plural': '[ Изображения товаров ]',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='subcategory',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='store.subcategory', verbose_name='Подгруппа'),
        ),
        migrations.CreateModel(
            name='OrderProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qty', models.PositiveIntegerField(default=1)),
                ('final_price', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Общая цена')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_products', to='store.order', verbose_name='Корзина')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.product', verbose_name='Товар')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(blank=True, related_name='related_cart', to='store.OrderProduct'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_orders', to=settings.AUTH_USER_MODEL, verbose_name='Автор'),
        ),
        migrations.AddField(
            model_name='customer',
            name='orders',
            field=models.ManyToManyField(related_name='related_order', to='store.Order', verbose_name='Заказы клиента'),
        ),
        migrations.AddField(
            model_name='customer',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
