from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payslip_list, name='list'),
    path('earnings/', views.earning_list, name='earning_list'),
    path('earnings/add/', views.earning_add, name='earning_add'),
    path('deductions/', views.deduction_list, name='deduction_list'),
    path('deductions/add/', views.deduction_add, name='deduction_add'),
    path('import/', views.import_payroll_excel, name='import_excel'),
    path('template/', views.download_payroll_template, name='download_template'),
]
