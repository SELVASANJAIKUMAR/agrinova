from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from matching.models import BuyerPreference
from matching.scoring import get_recommended_buyers_for_seller, get_recommended_sellers_for_buyer
from marketplace.models import Listing
from orders.models import Order, OrderItem


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['profile'] = user
        context['listings'] = Listing.objects.filter(seller=user, is_active=True).select_related('crop')[:5]
        context['orders'] = Order.objects.filter(buyer=user).prefetch_related('items__listing__crop')[:5]
        context['sales'] = OrderItem.objects.filter(
            listing__seller=user, order__payment_status='paid_test',
        ).select_related('order', 'listing__crop')[:5]

        pref = BuyerPreference.objects.filter(buyer=user).first()
        context['seller_recommendations'] = get_recommended_sellers_for_buyer(
            user,
            crop_id=pref.crop_id if pref else None,
            quantity_needed=pref.quantity_needed if pref else None,
            preferred_district=pref.preferred_district if pref else None,
            limit=3,
        )
        context['buyer_recommendations'] = get_recommended_buyers_for_seller(user, limit=3)
        return context
