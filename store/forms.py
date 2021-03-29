from django import forms
from django.contrib.auth import get_user_model

from .mixins import RequiredFieldsMixin
from .models import Order

User = get_user_model()


class PaymentMethodForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['payment_type', ]


class SelfOrderForm(RequiredFieldsMixin, forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            'payment_type', 'comment',
        ]


class CDEKOrderForm(RequiredFieldsMixin, forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            'address', 'last_name', 'first_name', 'patronymic', 'phone', 'comment',
        ]
        fields_required = ['address', 'last_name', 'first_name', 'phone']
        labels = {
            'address': 'Адрес пункта выдачи заказов CDEK',
        }


class CourierOrderForm(RequiredFieldsMixin, forms.ModelForm):
    class Meta:
        model = Order

        fields = (
            'address', 'last_name', 'first_name', 'patronymic', 'phone', 'comment',
        )
        fields_required = ['address', 'last_name', 'first_name', 'phone', ]
        labels = {
            'address': 'Адрес в Санкт-Петербурге',
            'phone': 'Телефон получателя',
        }
        widgets = ()


class PostRuOrderForm(RequiredFieldsMixin, forms.ModelForm):
    class Meta:
        model = Order

        fields = (
            'last_name', 'first_name', 'patronymic', 'phone', 'postal_code', 'settlement', 'address', 'comment',
        )
        fields_required = ['address', 'last_name', 'first_name', 'patronymic', 'phone', 'postal_code',
                           'settlement', ]
        labels = {
            'address': 'Адрес получателя',
        }


class PostWorldOrderForm(RequiredFieldsMixin, forms.ModelForm):
    class Meta:
        model = Order

        fields = (
            'first_name', 'last_name', 'patronymic', 'settlement', 'address', 'postal_code', 'phone', 'comment',
        )
        fields_required = ['last_name', 'first_name',
                           'settlement', 'address', ]
        labels = {
            'last_name': 'Фамилия (латинскими буквами)',
            'first_name': 'Имя (латинскими буквами)',
            'patronymic': 'Отчество (латинскими буквами)',
            'phone': 'Телефон',
            'postal_code': 'Индекс',
            'settlement': 'Страна, Город (латинскими буквами)',
            'address': 'Адрес получателя (латинскими буквами)',
            'comment': 'Комментарий',
            'payment_type': 'Тип оплаты',
        }


class CartForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('delivery_type',)


class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError(f'Пользователь с логином "{username} не найден в системе')
        user = User.objects.filter(username=username).first()
        if user:
            if not user.check_password(password):
                raise forms.ValidationError("Неверный пароль")
        return self.cleaned_data


class RegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин (имя в системе)'
        self.fields['password'].label = 'Пароль'
        self.fields['confirm_password'].label = 'Подтвердите пароль'
        self.fields['email'].label = 'Электронная почта'

    def clean_email(self):
        email = self.cleaned_data['email']
        # domain = email.split('.')[-1]
        # if domain in ['com', 'net']:
        #     raise forms.ValidationError(
        #         f'Регистрация для домена {domain} невозможна'
        #     )
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                f'Данный email уже зарегистрирован в системе'
            )
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                f'Имя {username} уже существует в системе, выберите другое'
            )
        return username

    def clean(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise forms.ValidationError('Пароли не совпадают')
        return self.cleaned_data

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'email']
