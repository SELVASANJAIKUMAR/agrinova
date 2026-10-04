
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View

from marketplace.models import Listing

from .cart import Cart
from .models import Order, OrderItem


@login_required
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart.html', {'cart': cart})


@login_required
def cart_add(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, is_active=True)
    cart = Cart(request)
    quantity = Decimal(request.POST.get('quantity', '1'))

    if quantity <= 0:
        messages.error(request, 'Quantity must be greater than zero.')
    elif quantity > listing.quantity:
        messages.error(
            request,
            f'Only {listing.quantity} {listing.unit} available.'
        )
    else:
        cart.add(listing, quantity)
        messages.success(
            request,
            f'Added {listing.crop.name} to cart.'
        )

    return redirect('marketplace:listing_detail', pk=listing_id)


@login_required
def cart_remove(request, listing_id):
    cart = Cart(request)
    cart.remove(listing_id)
    messages.success(request, 'Item removed from cart.')
    return redirect('orders:cart')


@login_required
def cart_update(request, listing_id):
    cart = Cart(request)
    quantity = Decimal(request.POST.get('quantity', '1'))
    cart.update(listing_id, quantity)
    return redirect('orders:cart')


class CheckoutView(LoginRequiredMixin, View):
    template_name = 'orders/checkout.html'

    def get(self, request):
        cart = Cart(request)

        if len(cart) == 0:
            messages.warning(request, 'Your cart is empty.')
            return redirect('marketplace:listing_list')

        return render(
            request,
            self.template_name,
            {'cart': cart}
        )

    def post(self, request):
        cart = Cart(request)

        if len(cart) == 0:
            messages.warning(request, 'Your cart is empty.')
            return redirect('marketplace:listing_list')

        order = Order.objects.create(
            buyer=request.user,
            status='pending',
            payment_status='unpaid',
            delivery_name=request.POST.get('delivery_name', ''),
            delivery_phone=request.POST.get('delivery_phone', ''),
            delivery_address=request.POST.get('delivery_address', ''),
            delivery_city=request.POST.get('delivery_city', ''),
            delivery_district=request.POST.get('delivery_district', ''),
            delivery_state=request.POST.get('delivery_state', ''),
            delivery_pincode=request.POST.get('delivery_pincode', ''),
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                listing=item['listing'],
                quantity=item['quantity'],
                unit_price=item['price'],
            )

        order.calculate_total()
        order.save()

        request.session['pending_order_id'] = order.id

        return redirect(
            'orders:payment',
            order_id=order.id
        )


class MockPaymentView(LoginRequiredMixin, View):
    template_name = 'orders/payment.html'

    def get(self, request, order_id):
        order = get_object_or_404(
            Order,
            id=order_id,
            buyer=request.user,
            payment_status='unpaid'
        )

        return render(
            request,
            self.template_name,
            {'order': order}
        )

    def post(self, request, order_id):
        order = get_object_or_404(
            Order,
            id=order_id,
            buyer=request.user,
            payment_status='unpaid'
        )

        order.payment_status = 'paid_test'
        order.status = 'confirmed'
        order.save()

        cart = Cart(request)
        cart.clear()

        request.session.pop('pending_order_id', None)

        messages.success(
            request,
            'Order placed — payment simulated successfully!'
        )

        return redirect(
            'orders:confirmation',
            order_id=order.id
        )


class OrderConfirmationView(LoginRequiredMixin, DetailView):
    model = Order
    pk_url_kwarg = 'order_id'
    template_name = 'orders/confirmation.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(
            buyer=self.request.user
        ).prefetch_related(
            'items__listing__crop'
        )


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(
            buyer=self.request.user
        ).prefetch_related(
            'items__listing__crop'
        )


class SalesHistoryView(LoginRequiredMixin, ListView):
    template_name = 'orders/sales_history.html'
    context_object_name = 'sales'

    def get_queryset(self):
        return OrderItem.objects.filter(
            listing__seller=self.request.user,
            order__payment_status='paid_test',
        ).select_related(
            'order',
            'listing__crop',
            'order__buyer'
        ).order_by(
            '-order__created_at'
        )


class OrderStatusUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    View
):
    """Allow seller or staff to update order status."""

    def test_func(self):
        order = get_object_or_404(
            Order,
            id=self.kwargs['order_id']
        )

        if self.request.user.is_staff:
            return True

        return order.items.filter(
            listing__seller=self.request.user
        ).exists()

    def post(self, request, order_id):
        order = get_object_or_404(
            Order,
            id=order_id
        )

        new_status = request.POST.get('status')

        valid_statuses = [
            s[0]
            for s in Order._meta.get_field('status').choices
        ]

        if new_status in valid_statuses:
            order.status = new_status
            order.save()

            messages.success(
                request,
                f'Order status updated to '
                f'{order.get_status_display()}.'
            )

        return redirect(
            request.META.get(
                'HTTP_REFERER',
                'dashboard:home'
            )
        )