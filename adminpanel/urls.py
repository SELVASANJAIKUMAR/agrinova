from django.urls import path

from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.manage_users, name='users'),
    path('listings/', views.manage_listings, name='listings'),
    path('orders/', views.manage_orders, name='orders'),
    path('ai-analytics/', views.ai_analytics, name='ai_analytics'),
]
