from django.db import models
from django.core.exceptions import ValidationError
from users.models import User


class Item(models.Model):
    CURRENCY_CHOICES = [
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='usd'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class Discount(models.Model):
    coupon_id = models.CharField(max_length=50, unique=True)
    percent_off = models.DecimalField(max_digits=5, decimal_places=2)
    duration = models.CharField(
        max_length=20,
        choices=[
            ('once', 'Once'),
            ('repeating', 'Repeating'),
            ('forever', 'Forever'),
        ]
    )

    def __str__(self):
        return f"{self.percent_off}% Discount ({self.coupon_id})"

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"


class Tax(models.Model):
    tax_id = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    inclusive = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.display_name} ({self.percentage}%)"

    class Meta:
        verbose_name = "Налог"
        verbose_name_plural = "Налоги"


class OrderItem(models.Model):
    """
    Промежуточная модель для связи Order и Item с указанием количества.
    """
    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.item.name}"


class Order(models.Model):
    items = models.ManyToManyField(
        'Item', through='OrderItem', related_name='orders')
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=Item.CURRENCY_CHOICES, default='usd')
    discount = models.ForeignKey(
        'Discount', on_delete=models.SET_NULL, null=True, blank=True)
    tax = models.ForeignKey(
        'Tax', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders')

    def __str__(self):
        return f"Order {self.id}"

    def add_item(self, item, quantity=1):
        """
        Добавляет товар в заказ.
        """
        order_item, created = OrderItem.objects.get_or_create(
            order=self, item=item)
        if not created:
            order_item.quantity += quantity
        else:
            order_item.quantity = quantity
        order_item.save()
        self.calculate_total_price()

    def remove_item(self, item):
        """
        Удаляет товар из заказа.
        """
        OrderItem.objects.filter(order=self, item=item).delete()
        self.calculate_total_price()

    def calculate_total_price(self):
        currencies = {item.currency for item in self.items.all()}
        if len(currencies) != 1:
            raise ValidationError(
                "Все товары в заказе должны быть в одной валюте!")
        self.currency = currencies.pop()

        subtotal = sum(
            order_item.item.price * order_item.quantity for order_item in self.order_items.all())

        if self.discount:
            subtotal *= (1 - self.discount.percent_off / 100)

        if self.tax:
            if not self.tax.inclusive:
                subtotal *= (1 + self.tax.percentage / 100)

        self.total_price = subtotal
        self.save()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
