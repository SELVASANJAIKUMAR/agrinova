from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:listing_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:listing_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:listing_id>/', views.cart_update, name='cart_update'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/<int:order_id>/', views.MockPaymentView.as_view(), name='payment'),
    path('confirmation/<int:order_id>/', views.OrderConfirmationView.as_view(), name='confirmation'),
    path('history/', views.OrderHistoryView.as_view(), name='history'),
    path('sales/', views.SalesHistoryView.as_view(), name='sales'),
    path('status/<int:order_id>/', views.OrderStatusUpdateView.as_view(), name='status_update'),
]
