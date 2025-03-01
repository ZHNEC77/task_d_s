from django.urls import path
from . import views

urlpatterns = [
    # Маршруты для товаров
    path('item/<int:id>/', views.item_detail, name='item_detail'),
    path('buy/item/<int:id>/', views.buy_item, name='buy_item'),

    # Маршруты для заказов
    path('order/create/', views.create_order, name='create_order'),
    path('order/<int:order_id>/add/', views.add_to_order, name='add_to_order'),
    path('order/<int:order_id>/remove/<int:item_id>/',
         views.remove_from_order, name='remove_from_order'),
    path('order/<int:id>/', views.order_detail, name='order_detail'),
    path('buy/order/<int:id>/', views.buy_order, name='buy_order'),

    # Маршруты для успешной оплаты и отмены
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
]
