# Generated by Django 3.1.7 on 2021-04-06 19:59

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_auto_20210406_1708'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='order',
            managers=[
                ('orders', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name='article',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Пункт меню'),
        ),
    ]
