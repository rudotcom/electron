from django.db import models


# def recalc_order(order):
#     cart_data = order.products.aggregate(models.Sum('final_price'), models.Count('id'))
#     if cart_data.get('final_price__sum'):
#         print(order.delivery_cost)
#         order.final_price = cart_data['final_price__sum'] + order.delivery_cost
#     else:
#         order.final_price = 0
#     order.total_products = cart_data['id__count']
#     order.save()
