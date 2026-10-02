from django.urls import path

from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.ListingListView.as_view(), name='listing_list'),
    path('add/', views.ListingCreateView.as_view(), name='listing_create'),
    path('<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('<int:pk>/edit/', views.ListingUpdateView.as_view(), name='listing_edit'),
    path('<int:pk>/delete/', views.ListingDeleteView.as_view(), name='listing_delete'),
]
