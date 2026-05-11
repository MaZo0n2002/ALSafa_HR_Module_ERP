from django.urls import path
from . import views

app_name = 'zkteco'

urlpatterns = [
    path('devices/', views.device_list, name='device_list'),
    path('sync/<int:device_id>/', views.sync_device, name='sync_device'),
    path('users/<int:device_id>/', views.device_users, name='device_users'),
    path('link/<int:device_id>/<int:user_id>/', views.link_user, name='link_user'),
]
