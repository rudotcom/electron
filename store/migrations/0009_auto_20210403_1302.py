# Generated by Django 3.1.7 on 2021-04-03 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_auto_20210403_1234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parameter',
            name='value',
            field=models.TextField(max_length=50, verbose_name='Значение'),
        ),
    ]
