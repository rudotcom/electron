# Generated by Django 3.1.7 on 2021-03-19 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_type',
            field=models.CharField(choices=[('cash_card', 'Наличные или банковская карта в мастерской'), ('bankcard', 'Банковская карта онлайн'), ('kiwi', 'Киви кошелёк / Paypal')], default=None, max_length=100, null=True, verbose_name='Способ оплаты'),
        ),
    ]
