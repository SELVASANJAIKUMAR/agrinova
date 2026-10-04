from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('user/', views.user_report, name='user_report'),
    path('buy/', views.buy_report, name='buy_report'),
    path('sell/', views.sell_report, name='sell_report'),
    path('chatbot/', views.chatbot_report, name='chatbot_report'),
    path('forecast/', views.forecast_report, name='forecast_report'),
    path('combined/', views.combined_report, name='combined_report'),
]