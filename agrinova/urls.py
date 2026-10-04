"""URL configuration for agrinova project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views.static import serve
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_required(TemplateView.as_view(template_name='home.html')), name='home'),
    path('accounts/', include('accounts.urls')),
    path('marketplace/', include('marketplace.urls')),
    path('orders/', include('orders.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('forecasting/', include('forecasting.urls')),
    path('matching/', include('matching.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('adminpanel/', include('adminpanel.urls')),
    path('reports/', include('reports.urls')),
]

urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]

handler404 = 'agrinova.views.handler404'
handler500 = 'agrinova.views.handler500'