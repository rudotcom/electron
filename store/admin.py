import datetime

from PIL import Image
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db.models import Q
from django.forms import ModelForm, ValidationError
from django.contrib import admin
from django.template.loader import render_to_string
from django.utils.html import mark_safe

from store.models import Category, SubCategory, Product, ProductImage, Order, OrderProduct, User, Customer


class ProductAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['image'].help_text = mark_safe(
            '<i>Минимальный размер {}x{}, максимальный {}x{}, 3 Мб</i>'.format(
                *Product.MIN_DIMENSIONS, *Product.MAX_DIMENSIONS
            )
        )
        # instance = kwargs.get('instance')
        #
        # if not instance.quantity:
        #     self.fields['display'].help_text = 'Изменять при количестве больше 0'
        #     self.fields['display'].widget.attrs.update({
        #         'style': 'background: #eee; color: #aaa', 'readonly': True,
        #     })

    # def clean(self):  # Обращение ко всем полям
    # if self.cleaned_data['quantity'] == 0:
    # self.cleaned_data['price'].help_text = 'Изменять при количестве больше 0'
    # return self.cleaned_data

    def clean_image(self):  # Работа с полем image
        min_width, min_height = Product.MIN_DIMENSIONS
        max_width, max_height = Product.MAX_DIMENSIONS
        image = self.cleaned_data['image']
        img = Image.open(image)

        if image.size > Product.MAX_IMAGE_SIZE:
            raise ValidationError('Размер файла изображения превышает допустимые 3 Мб')
        if img.height < min_height or img.width < min_width:
            raise ValidationError('Размер загруженного изображения меньше допустимого {}x{}'.format(
                *Product.MIN_DIMENSIONS))
        if img.height > max_height or img.width > max_width:
            raise ValidationError('Размер загруженного изображения больше допустимого {}x{}'.format(
                *Product.MAX_DIMENSIONS))
        return image


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    change_form_template = 'admin.html'
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = [
        ('Товар',
         {'fields': ['title', 'category', 'subcategory', 'price', 'price_discount', 'quantity',
                     ('image', 'image_tag',), 'description', 'display', ]}
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
    readonly_fields = ['image_tag', 'visits', 'last_visit', 'date_added', ]
    list_display = ('title', 'image_tag', 'category', 'subcategory', 'price', 'quantity',
                    'bestseller', 'new', 'display', 'visits')
    list_filter = ['category', 'subcategory', 'bestseller']
    search_fields = ['title', 'description']
    ordering = ('-date_added', 'title', 'category', 'price', 'new', 'quantity')


class SubCategoryAdmin(admin.ModelAdmin):
    fields = ['category', 'name', 'slug']
    list_display = ('name', 'category')
    list_filter = ['category']


class CustomerAdmin(admin.ModelAdmin):
    fields = ['session', 'user', 'phone', 'address']
    list_display = ('session', 'user', 'created')
    ordering = ('-created',)


def admin_order_shipped(modeladmin, request, queryset):
    user = User.objects.get(username=request.user)
    for order in queryset:
        order.shipped_date = datetime.datetime.now()
        order.status = Order.STATUS_SHIPPED
        order.save()

        html = render_to_string('order_sent.html', {'order': order})
        send_mail('Order sent', 'Ваш заказ отправлен!', 'noreply@introvert.com.ru', [user.email],
                  fail_silently=False, html_message=html)
    return


# admin_order_shipped.short_description = 'Set shipped'


class OrderItemInline(admin.TabularInline):
    model = OrderProduct
    fields = ['product', 'image_tag', 'qty', 'final_price', ]
    readonly_fields = ['product', 'image_tag', 'qty', 'final_price', ]
    can_delete = False
    extra = 0
    max_num = 0
    # raw_id_fields = ['product']


class OrderAdmin(admin.ModelAdmin):
    fields = ['owner', 'created_at', 'buying_type', 'address', 'phone', 'comment', 'status', ]
    readonly_fields = ['created_at', 'owner', 'buying_type', 'address', 'phone', 'comment']
    list_display = ('id', 'status', 'final_price', 'total_products', 'buying_type', 'owner', 'created_at')
    ordering = ('-created_at', 'owner', 'status', 'buying_type',)
    list_filter = ('status', 'buying_type', 'created_at', )
    inlines = [OrderItemInline]


class ProductImageAdmin(admin.ModelAdmin):
    fields = ['product', 'image_tag', 'image', ]
    readonly_fields = ['image_tag']
    list_display = ('product', 'image_tag',)
    ordering = ('product',)


admin.site.site_header = "Панель управления магазина INTROVERT"
admin.site.unregister(Group)
admin.site.register(Category)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Order, OrderAdmin)

# admin.site.register(Customer, CustomerAdmin)
