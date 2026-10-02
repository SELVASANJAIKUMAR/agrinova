from django.urls import path

from . import views

app_name = 'forecasting'

urlpatterns = [
    path('', views.forecast_page, name='forecast'),
]
