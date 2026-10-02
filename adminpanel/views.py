from collections import Counter
import re

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from chatbot.models import ChatLog
from marketplace.models import Listing
from orders.models import Order


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff or u.is_superuser)(view_func)


@staff_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_listings = Listing.objects.filter(is_active=True).count()
    total_orders = Order.objects.filter(payment_status='paid_test').count()

    orders_over_time = (
        Order.objects.filter(payment_status='paid_test')
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    return render(request, 'adminpanel/dashboard.html', {
        'total_users': total_users,
        'total_listings': total_listings,
        'total_orders': total_orders,
        'orders_over_time': list(orders_over_time),
    })


@staff_required
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = get_object_or_404(User, id=user_id)
        if action == 'disable':
            user.is_active_account = False
            user.is_active = False
        elif action == 'enable':
            user.is_active_account = True
            user.is_active = True
        user.save()
        return redirect('adminpanel:users')
    return render(request, 'adminpanel/users.html', {'users': users})


@staff_required
def manage_listings(request):
    listings = Listing.objects.select_related('crop', 'seller').order_by('-created_at')
    if request.method == 'POST':
        listing_id = request.POST.get('listing_id')
        action = request.POST.get('action')
        listing = get_object_or_404(Listing, id=listing_id)
        if action == 'deactivate':
            listing.is_active = False
            listing.save()
        elif action == 'activate':
            listing.is_active = True
            listing.save()
        return redirect('adminpanel:listings')
    return render(request, 'adminpanel/listings.html', {'listings': listings})


@staff_required
def manage_orders(request):
    orders = Order.objects.select_related('buyer').prefetch_related('items__listing__crop').order_by('-created_at')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        valid = [s[0] for s in Order._meta.get_field('status').choices]
        if new_status in valid:
            order.status = new_status
            order.save()
        return redirect('adminpanel:orders')
    return render(request, 'adminpanel/orders.html', {'orders': orders})


@staff_required
def ai_analytics(request):
    total_queries = ChatLog.objects.count()
    provider_stats = (
        ChatLog.objects.values('provider')
        .annotate(count=Count('id'), avg_time=Avg('response_time_ms'))
        .order_by('-count')
    )
    avg_response = ChatLog.objects.aggregate(avg=Avg('response_time_ms'))['avg'] or 0

    # Simple keyword frequency from queries
    words = []
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'how', 'what', 'can', 'i', 'my', 'for', 'to', 'in', 'of', 'and', 'or'}
    for log in ChatLog.objects.values_list('query', flat=True)[:500]:
        tokens = re.findall(r'[a-zA-Z]{3,}', log.lower())
        words.extend(w for w in tokens if w not in stopwords)
    top_topics = Counter(words).most_common(15)

    recent_logs = ChatLog.objects.select_related('user').order_by('-created_at')[:20]

    return render(request, 'adminpanel/ai_analytics.html', {
        'total_queries': total_queries,
        'provider_stats': provider_stats,
        'avg_response': round(avg_response, 1),
        'top_topics': top_topics,
        'recent_logs': recent_logs,
    })
