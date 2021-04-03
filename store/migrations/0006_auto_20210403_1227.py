# Generated by Django 3.1.7 on 2021-04-03 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_auto_20210331_2005'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Параметр')),
                ('value', models.DecimalField(decimal_places=2, default=0, max_digits=9, verbose_name='Значение')),
                ('meaning', models.CharField(blank=True, max_length=255, null=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Параметр',
                'verbose_name_plural': 'Параметры',
                'ordering': ('title',),
            },
        ),
        migrations.AlterModelOptions(
            name='article',
            options={'ordering': ('id',), 'verbose_name': 'Страница', 'verbose_name_plural': 'Страницы'},
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('id',), 'verbose_name': 'Группа', 'verbose_name_plural': 'Группы'},
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': 'Заказ', 'verbose_name_plural': '1. Заказы'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ('subcategory', 'title'), 'verbose_name': 'Товар', 'verbose_name_plural': '2. Товары'},
        ),
        migrations.AlterModelOptions(
            name='subcategory',
            options={'ordering': ('category', 'name'), 'verbose_name': 'Подгруппа', 'verbose_name_plural': 'Подгруппы'},
        ),
    ]
