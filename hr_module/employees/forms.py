from django import forms
from .models import Employee, Department, Position

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_code', 'full_name', 'branch', 'department', 'job_title', 
            'basic_salary', 'hire_date', 'zkteco_id', 'bank_number', 'status',
            'requires_attendance_tracking', 'is_active', 'user'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Apply styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'sr-only peer'
            elif not isinstance(field.widget, (forms.RadioSelect, forms.Select)):
                field.widget.attrs['class'] = 'form-input'
            else:
                field.widget.attrs['class'] = 'form-input p-2'

        self.fields['employee_code'].required = False
        self.fields['employee_code'].widget.attrs['readonly'] = True
        self.fields['employee_code'].widget.attrs['placeholder'] = 'Auto-generated on save'

        # Departments are now Global
        self.fields['department'].queryset = Department.objects.all()
        self.fields['department'].label_from_instance = lambda obj: obj.name

        # Branch Isolation
        if user and user.branch:
            # If user has a branch, they can only see their branch in the dropdown
            from accounts.models import Branch
            self.fields['branch'].queryset = Branch.objects.filter(id=user.branch.id)
            self.fields['branch'].initial = user.branch
            self.fields['branch'].empty_label = None # Prevent selecting empty if they have a branch
            
            # If editing an existing employee from another branch (security check)
            if self.instance and self.instance.pk and self.instance.branch != user.branch:
                # This should ideally be handled in the view, but let's be safe
                self.fields['branch'].disabled = True
