from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()

class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.status != 'Active':
            raise ValidationError(
                "Your account is not active. Please contact the administrator.",
                code='inactive',
            )
        if user.role not in ['Admin', 'HR']:
            raise ValidationError(
                "Access restricted to HR personnel.",
                code='role_denied',
            )

class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, label="Full Name")
    email = forms.EmailField(required=True, label="Email Address")
    role = forms.ChoiceField(choices=[('Admin', 'Admin'), ('HR', 'HR')], required=True)
    employee_code = forms.CharField(max_length=20, required=False, label="Employee Code (Optional)")

    class Meta:
        model = User
        fields = ("full_name", "email", "role", "employee_code")

    def clean_employee_code(self):
        code = self.cleaned_data.get('employee_code')
        if code:
            from employees.models import Employee
            if Employee.objects.filter(employee_code=code, user__isnull=False).exists():
                raise forms.ValidationError("This employee is already linked to another account.")
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.full_name = self.cleaned_data["full_name"]
        user.is_active = False # New users are inactive until approved
        if commit:
            user.save()
        return user

class UserEditForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('Admin', 'Admin'), ('HR', 'HR')], required=True)
    
    class Meta:
        model = User
        fields = ('email', 'full_name', 'role', 'status')
