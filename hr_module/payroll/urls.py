from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payslip_list, name='list'),
    path('earnings/', views.earning_list, name='earning_list'),
    path('earnings/add/', views.earning_add, name='earning_add'),
    path('earnings/edit/<int:pk>/', views.earning_edit, name='earning_edit'),
    path('earnings/delete/<int:pk>/', views.earning_delete, name='earning_delete'),
    path('deductions/', views.deduction_list, name='deduction_list'),
    path('deductions/add/', views.deduction_add, name='deduction_add'),
    path('deductions/edit/<int:pk>/', views.deduction_edit, name='deduction_edit'),
    path('deductions/delete/<int:pk>/', views.deduction_delete, name='deduction_delete'),
    path('import/', views.import_payroll_excel, name='import_excel'),
    path('export/', views.export_payroll_excel, name='export_excel'),
    path('template/', views.download_payroll_template, name='download_template'),
    path('payslip/<int:pk>/', views.payslip_detail, name='detail'),
    path('payslip/<int:pk>/recalculate/', views.recalculate_payslip, name='recalculate'),
    path('generate/', views.generate_payroll, name='generate'),
]
