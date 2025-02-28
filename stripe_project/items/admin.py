from django.contrib import admin
from .models import Item, Order, OrderItem, Discount, Tax


# Кастомизация админки для модели OrderItem (встроенное отображение в Order)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Количество пустых форм для добавления новых товаров


class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')
    list_filter = ('price',)
    search_fields = ('name', 'description')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_price', 'discount', 'tax')
    list_filter = ('discount', 'tax')
    inlines = [OrderItemInline]  # Встроенное отображение товаров заказа


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('coupon_id', 'percent_off', 'duration')
    search_fields = ('coupon_id',)


class TaxAdmin(admin.ModelAdmin):
    list_display = ('tax_id', 'display_name', 'percentage',
                    'inclusive')
    list_filter = ('inclusive',)
    search_fields = ('tax_id', 'display_name')


admin.site.register(Item, ItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(Tax, TaxAdmin)
