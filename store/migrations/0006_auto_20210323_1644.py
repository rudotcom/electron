# Generated by Django 3.1.7 on 2021-03-23 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_auto_20210320_1901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='care',
            field=models.TextField(null=True, verbose_name='Инструкция по уходу'),
        ),
    ]
