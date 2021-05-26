from django import forms
from PIL import Image
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.forms import ModelForm, ValidationError
from django.template.loader import render_to_string
from django.utils.html import mark_safe
from ckeditor.widgets import CKEditorWidget

from store.models import Group, Category, Product, Order, \
    OrderProduct, Article, Customer


class ProductAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Товар',
         {'fields': ['article', 'title', 'category', 'price',
                     ('warehouse1', 'warehouse2'),
                     ('image', 'image_thumb',), 'display', ]}
         ),
    ]
    readonly_fields = ['image_thumb', ]
    list_display = ('id', 'article', 'title', 'image_thumb', 'category', 'price',
                    'display', 'quantity')
    list_filter = ['display', 'category', ]
    search_fields = ['article', 'title']
    ordering = ('title', 'category', 'price')


class CategoryProductInline(admin.TabularInline):
    model = Product
    fields = ['article', 'title', 'image_thumb', 'price', 'warehouse1', 'warehouse2', ]
    readonly_fields = ['article', 'title', 'image_thumb', 'price', 'warehouse1', 'warehouse2', ]
    can_delete = False
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    fields = ['id', 'parent', 'name', ]
    list_display = ('name', 'parent',)
    list_filter = ['parent']
    inlines = [CategoryProductInline]
    CategoryProductInline.verbose_name = 'Товар'


class GroupCategoryInline(admin.TabularInline):
    model = Category
    fields = ['id', 'name', ]
    readonly_fields = ['id', 'name', ]
    can_delete = False
    extra = 0


class GroupAdmin(admin.ModelAdmin):
    fields = ['id', 'name', ]
    list_display = ('name',)
    inlines = [GroupCategoryInline]
    GroupCategoryInline.verbose_name = 'Категория'


class CustomerAdmin(admin.ModelAdmin):
    fields = ['session', 'user', 'phone', 'confirmed']
    list_display = ('session', 'user', 'created', 'confirmed')
    ordering = ('-created',)


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
              'created_at', 'phone', 'comment', 'total_price_net',
              'status', 'remark',)
    readonly_fields = ['created_at', 'comment', 'owner', 'total_price_net', ]
    list_display = ('id', 'status', 'total_products', 'get_fio', 'created_at')
    list_display_links = ('id', 'status')
    ordering = ('-created_at', 'owner', 'status',)
    list_filter = ('status', 'created_at',)
    inlines = [OrderItemInline]


class ArticleAdminForm(forms.ModelForm):
    title = forms.CharField(label='Заголовок', max_length=200)
    content = forms.CharField(label='Текст страницы', widget=CKEditorWidget())


class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm

    fieldsets = (
        (None, {'fields': ('slug', 'name', 'title', 'content',)}),
    )
    list_display = ('name', 'title', 'slug',)


admin.site.site_header = "Панель управления магазина INTROVERT"
# admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Article, ArticleAdmin)

# admin.site.register(Customer, CustomerAdmin)
