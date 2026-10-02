from decimal import Decimal

import pytest

from orders.models import Order, OrderItem


@pytest.mark.django_db
class TestOrderModels:
    def test_line_total(self, listing):
        order = Order.objects.create(buyer=listing.seller)
        item = OrderItem.objects.create(
            order=order, listing=listing, quantity=10, unit_price=30,
        )
        assert item.line_total == Decimal('300')

    def test_calculate_total(self, user, listing):
        order = Order.objects.create(buyer=user)
        OrderItem.objects.create(order=order, listing=listing, quantity=5, unit_price=30)
        total = order.calculate_total()
        assert total == Decimal('150')
        assert order.total_amount == Decimal('150')


@pytest.mark.django_db
class TestOrderFlow:
    def test_full_checkout_flow(self, client, user, listing):
        client.login(username='testuser', password='testpass123')
        client.post(f'/orders/cart/add/{listing.id}/', {'quantity': '2'})
        resp = client.post('/orders/checkout/')
        assert resp.status_code == 302
        order = Order.objects.filter(buyer=user).first()
        assert order is not None
        resp = client.post(f'/orders/payment/{order.id}/', follow=True)
        assert resp.status_code == 200
        assert 'confirmation' in resp.redirect_chain[0][0]
        order.refresh_from_db()
        assert order.payment_status == 'paid_test'
        assert order.status == 'confirmed'
        assert resp.context['order'].id == order.id

    def test_confirmation_page_direct_access(self, client, user, listing):
        client.login(username='testuser', password='testpass123')
        order = Order.objects.create(buyer=user, status='confirmed', payment_status='paid_test', total_amount=Decimal('60.00'))
        resp = client.get(f'/orders/confirmation/{order.id}/')
        assert resp.status_code == 200
        assert resp.context['order'].id == order.id
        assert f'Order #{order.id}' in resp.content.decode()

    def test_order_history_page(self, client, user, listing):
        client.login(username='testuser', password='testpass123')
        order = Order.objects.create(buyer=user, status='confirmed', payment_status='paid_test', total_amount=Decimal('60.00'))
        resp = client.get('/orders/history/')
        assert resp.status_code == 200
        assert order in resp.context['orders']
