from django.urls import path
from . import views

app_name = 'leaves'

urlpatterns = [
    path('', views.leave_list, name='list'),
    path('request/', views.leave_request, name='request'),
    path('approve/<int:pk>/', views.leave_approve, name='approve'),
    path('reject/<int:pk>/', views.leave_reject, name='reject'),
]
