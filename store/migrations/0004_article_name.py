# Generated by Django 3.1.7 on 2021-03-31 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_auto_20210331_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='name',
            field=models.CharField(max_length=50, null=True, verbose_name='Пункт меню'),
        ),
    ]
