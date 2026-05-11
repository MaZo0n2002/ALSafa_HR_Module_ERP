from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import UserRegisterForm, UserEditForm
from audit.models import AuditLog
from .decorators import role_required
from employees.models import Employee

User = get_user_model()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@role_required(['Admin'])
def create_user(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.status = 'Active' # Internal users are active by default
            user.save()
            
            employee_code = form.cleaned_data.get('employee_code')
            if employee_code:
                try:
                    employee = Employee.objects.get(employee_code=employee_code)
                    employee.user = user
                    employee.save()
                except Employee.DoesNotExist:
                    pass

            AuditLog.objects.create(
                user=request.user,
                action=f"Created user {user.email}",
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'User {user.email} created successfully.')
            return redirect('accounts:admin_dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/create_user.html', {'form': form})

@role_required(['Admin'])
def admin_dashboard(request):
    users = User.objects.all().order_by('-created_at')
    if request.user.branch:
        users = users.filter(branch=request.user.branch)
    return render(request, 'accounts/admin_dashboard.html', {'users': users})

@role_required(['Admin'])
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.status = 'Active'
    user.save() # save() override handles is_active=True
    messages.success(request, f'User {user.email} approved.')
    return redirect('accounts:admin_dashboard')

@role_required(['Admin'])
def reject_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.status = 'Rejected'
    user.save() # save() override handles is_active=False
    messages.success(request, f'User {user.email} rejected.')
    return redirect('accounts:admin_dashboard')

@role_required(['Admin'])
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        email = user.email
        user.delete()
        messages.success(request, f'User {email} deleted.')
    return redirect('accounts:admin_dashboard')

@role_required(['Admin'])
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.email} updated.')
            return redirect('accounts:admin_dashboard')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'accounts/edit_user.html', {'form': form, 'edit_user': user})
