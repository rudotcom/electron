from datetime import datetime
from django import forms
from PIL import Image
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.forms import ModelForm, ValidationError
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from ckeditor.widgets import CKEditorWidget

from store.models import Category, SubCategory, Product, ProductImage, Order, \
    OrderProduct, User, Article, Parameter


class ProductAdminForm(ModelForm):
    description = forms.CharField(label='Описание', widget=CKEditorWidget())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['image'].help_text = mark_safe(
            '<i>Минимальный размер {}x{}</i>'.format(
                *Product.PRODUCT_CARD
            )
        )

    # def clean(self):  # Обращение ко всем полям
    # if self.cleaned_data['quantity'] == 0:
    # self.cleaned_data['price'].help_text = 'Изменять при количестве больше 0'
    # return self.cleaned_data

    def clean_image(self):  # Работа с полем image
        min_width, min_height = Product.PRODUCT_CARD
        image = self.cleaned_data['image']
        img = Image.open(image)

        if image.size > Product.MAX_IMAGE_SIZE:
            raise ValidationError(
                'Размер файла изображения превышает допустимые 4 Мб'
            )
        if img.height < min_height or img.width < min_width:
            raise ValidationError(
                'Размер загруженного изображения меньше допустимого {}x{}'
                .format(*Product.PRODUCT_CARD)
            )
        return image


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    fields = ['product', 'image_thumb', 'image', ]
    readonly_fields = ['product', 'image_thumb', ]
    can_delete = True
    extra = 0
    # max_num = 0


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    change_form_template = 'admin.html'
    prepopulated_fields = {"slug": ("title",)}
    radio_fields = {"gender": admin.HORIZONTAL}

    fieldsets = [
        ('Товар',
         {'fields': ['title', 'category', 'subcategory', 'price',
                     'price_discount', 'quantity',
                     ('image', 'image_thumb',), 'description', 'display', ]}
         ),
        ('Параметры',
         {'fields': ['length', 'width', 'height', 'material', 'color'],
          'classes': ['collapse']}
         ),
        ('Инструкции',
         {'fields': ['care', ],
          'classes': ['collapse']}
         ),
        ('Целевые группы',
         {'fields': ['gender', 'gift', 'bestseller', 'limited', 'new'],
          'classes': ['collapse']}
         ),
        ('Служебная информация',
         {'fields': ['slug', 'date_added', 'visits', 'last_visit', ],
          'classes': ['collapse']}
         ),
    ]
    readonly_fields = ['image_thumb', 'visits', 'last_visit', 'date_added', ]
    list_display = ('title', 'image_thumb', 'visits', 'category', 'price',
                    'price_discount', 'quantity',
                    'bestseller', 'new', 'display')
    list_filter = ['bestseller', 'new', 'display', ]
    search_fields = ['title', 'description']
    ordering = ('-date_added', 'title', 'category', 'price', 'new', 'quantity')
    inlines = [ProductImageInline]
    ProductImageInline.verbose_name = 'Изображение'


class SubCategoryAdmin(admin.ModelAdmin):
    fields = ['category', 'name', 'count', 'slug']
    list_display = ('name', 'category', 'count')
    readonly_fields = ['count']
    list_filter = ['category']
    prepopulated_fields = {"slug": ("name",)}


class CustomerAdmin(admin.ModelAdmin):
    fields = ['session', 'user', 'phone', 'address', 'confirmed']
    list_display = ('session', 'user', 'created', 'confirmed')
    ordering = ('-created',)


def admin_order_shipped(modeladmin, request, queryset):
    user = User.objects.get(username=request.user)
    for order in queryset:
        order.shipped_date = datetime.now()
        order.status = Order.STATUS_SHIPPED
        order.save()

        html = render_to_string('order_sent.html', {'order': order})
        send_mail('Order sent', 'Ваш заказ отправлен!',
                  'noreply@introvert.com.ru', [user.email],
                  fail_silently=False, html_message=html)
    return


# admin_order_shipped.short_description = 'Set shipped'


class OrderItemInline(admin.TabularInline):
    model = OrderProduct
    fields = ['product', 'image_thumb', 'qty', 'final_price', ]
    readonly_fields = ['product', 'image_thumb', 'qty', 'final_price', ]
    can_delete = False
    extra = 0
    max_num = 0
    # raw_id_fields = ['product']


class OrderAdmin(admin.ModelAdmin):
    fields = ('last_name', ('first_name', 'patronymic'), 'owner',
              'created_at', 'phone', 'delivery_type', 'postal_code',
              'settlement', 'address', 'comment', 'total_price_net',
              'delivery_cost', 'total_price_gross',
              ('payment_id', 'payment_status', 'payment_time'),
              ('status', 'is_paid'),
              'tracking', 'remark', 'gift',)
    readonly_fields = ['created_at', 'delivery_type', 'delivery_cost',
                       'comment', 'owner', 'gift', 'total_price_net',
                       'total_price_gross', 'payment_id', 'payment_status',
                       'payment_time']
    list_display = ('id', 'delivery_type', 'status', 'payment_status',
                    'is_paid', 'total_products', 'total_price_gross',
                    'get_fio', 'created_at')
    list_display_links = ('id', 'delivery_type', 'status')
    ordering = ('-created_at', 'owner', 'status', 'delivery_type',)
    list_filter = ('status', 'payment_status', 'delivery_type', 'created_at',)
    inlines = [OrderItemInline]

    # def formfield_for_choice_field(self, db_field, request, **kwargs):
    #     if db_field.name == "status":
    #         kwargs['choices'] = (
    #             ('new', 'Оформлен'),
    #             ('paid', 'Оплачен'),
    #             ('in_progress', 'В обработке'),
    #             ('is_ready', 'Готов'),
    #             ('shipped', 'Отправлен'),
    #             ('delivered', 'Доставлен в место выдачи'),
    #             ('received', 'Получен'),
    #             ('return', 'Возврат'),
    #             ('canceled', 'Отменен'),
    #         )
    #
    #     return super().formfield_for_choice_field(
    #         db_field, request, **kwargs
    #     )


class ProductImageAdmin(admin.ModelAdmin):
    fields = ['product', 'image', ]
    list_display = ('product', 'image_thumb',)
    ordering = ('product',)


class ArticleAdminForm(forms.ModelForm):
    title = forms.CharField(label='Заголовок', max_length=200)
    content = forms.CharField(label='Текст страницы', widget=CKEditorWidget())


class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm

    fieldsets = (
        (None, {'fields': ('slug', 'name', 'title', 'content',)}),
    )
    list_display = ('name', 'title', 'slug',)


class ParameterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'value', 'meaning',)}),
    )
    readonly_fields = ['name', ]
    list_display = ('name', 'value',)

    # убрать кнопку "Удалить"
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = "Панель управления магазина INTROVERT"
admin.site.unregister(Group)
admin.site.register(Category)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Parameter, ParameterAdmin)

# admin.site.register(ProductImage, ProductImageAdmin)
# admin.site.register(Customer, CustomerAdmin)
