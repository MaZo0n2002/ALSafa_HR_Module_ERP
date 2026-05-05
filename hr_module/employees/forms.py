from django import forms
from .models import Employee, Department, Position

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_code', 'full_name', 'department', 'job_title', 'basic_salary', 'hire_date', 'zkteco_id', 'is_active', 'user']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }
