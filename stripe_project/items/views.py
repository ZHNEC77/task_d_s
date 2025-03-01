from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import stripe
from django.conf import settings
from .models import Item, Order, OrderItem, Discount, Tax
from django.contrib.auth.decorators import login_required
from .forms import AddToOrderForm
from users.models import User
# stripe.api_key = settings.STRIPE_SECRET_KEY


def get_stripe_keys(currency):
    """Возвращает соответствующие ключи Stripe в зависимости от валюты."""
    if currency == 'usd':
        return settings.STRIPE_SECRET_KEY_USD, settings.STRIPE_PUBLIC_KEY_USD
    elif currency == 'eur':
        return settings.STRIPE_SECRET_KEY_EUR, settings.STRIPE_PUBLIC_KEY_EUR
    else:
        raise ValueError(f"Unsupported currency: {currency}")


def item_detail(request, id):
    """
    View для отображения страницы товара.
    """
    item = get_object_or_404(Item, id=id)
    _, public_key = get_stripe_keys(item.currency)
    return render(request, 'items/item_detail.html', {
        'item': item,
        'STRIPE_PUBLIC_KEY': public_key,
    })


@login_required
def buy_item(request, id):
    """
    View для создания Stripe Checkout Session для оплаты одного товара.
    """
    item = get_object_or_404(Item, id=id, user=request.user)
    secret_key, _ = get_stripe_keys(item.currency)
    stripe.api_key = secret_key

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': item.currency,
                'product_data': {
                    'name': item.name,
                },
                'unit_amount': int(item.price * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/success/'),
        cancel_url=request.build_absolute_uri('/cancel/'),
    )
    return JsonResponse({'session_id': session.id})


@login_required
def create_order(request):
    """
    View для создания нового заказа.
    """
    order = Order.objects.create(user=request.user)
    return redirect('order_detail', id=order.id)


@login_required
def add_to_order(request, order_id):
    """
    View для добавления товара в заказ.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        form = AddToOrderForm(request.POST, user=request.user)
        if form.is_valid():
            item = form.cleaned_data['item']
            quantity = form.cleaned_data['quantity']
            OrderItem.objects.create(order=order, item=item, quantity=quantity)
            return redirect('order_detail', id=order.id)
    else:
        form = AddToOrderForm(user=request.user)
    return render(request, 'items/add_to_order.html', {'form': form, 'order': order})


@login_required
def remove_from_order(request, order_id, item_id):
    """
    View для удаления товара из заказа.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_item = get_object_or_404(OrderItem, order=order, item_id=item_id)
    order_item.delete()
    return redirect('order_detail', id=order.id)


@login_required
def order_detail(request, id):
    """
    View для отображения страницы заказа.
    """
    order = get_object_or_404(Order, id=id, user=request.user)
    order.calculate_total_price()
    _, public_key = get_stripe_keys(order.currency)
    return render(request, 'items/order_detail.html', {
        'order': order,
        'STRIPE_PUBLIC_KEY': public_key,
    })


@login_required
def buy_order(request, id):
    """
    View для создания Stripe Checkout Session для оплаты заказа.
    """
    order = get_object_or_404(Order, id=id, user=request.user)
    order.calculate_total_price()
    secret_key, _ = get_stripe_keys(order.currency)
    stripe.api_key = secret_key

    # Создаем список товаров для Stripe Checkout
    line_items = []
    for order_item in order.order_items.all():
        line_items.append({
            'price_data': {
                'currency': order.currency,
                'product_data': {
                    'name': order_item.item.name,
                },
                'unit_amount': int(order_item.item.price * 100),
            },
            'quantity': order_item.quantity,
        })

    checkout_params = {
        'payment_method_types': ['card'],
        'line_items': line_items,
        'mode': 'payment',
        'success_url': request.build_absolute_uri('/success/'),
        'cancel_url': request.build_absolute_uri('/cancel/'),
    }

    if order.discount:
        checkout_params['discounts'] = [{'coupon': order.discount.coupon_id}]

    if order.tax:
        checkout_params['automatic_tax'] = {'enabled': True}

    session = stripe.checkout.Session.create(**checkout_params)
    return JsonResponse({'session_id': session.id})


def success(request):
    return render(request, 'items/success.html')


def cancel(request):
    return render(request, 'items/cancel.html')
