from django.urls import path

from store.views import (
    GroupListView,
    ProductDetailView,
    GroupDetailView,
    CartView,
    AddToCartView,
    DeleteFromCartView,
    ChangeQTYView,
    MakeOrderView,
    ProductSearchView,
    CategoryDetailView,
    EmailView,
)

urlpatterns = [
    path('', GroupListView.as_view(), name='group_list'),
    path('search/', ProductSearchView.as_view(), name='search'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('group/<int:pk>/', GroupDetailView.as_view(), name='group_detail'),
    path('category/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/<int:pk>/', AddToCartView.as_view(), name='add_to_cart'),
    path('remove-from-cart/<int:pk>/', DeleteFromCartView.as_view(), name='delete_from_cart'),
    path('change-qty/<int:pk>/', ChangeQTYView.as_view(), name='change_qty'),
    path('checkout/', MakeOrderView.as_view(), name='checkout'),
    # path('order_email/<int:order>/', EmailView.as_view(), name='order_email'),
]
