from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from accounts.decorators import role_required
from .models import Employee
from .forms import EmployeeForm

from django.db.models import Q
from .models import Employee, Department

@login_required
@role_required(['Admin', 'HR'])
def employee_list(request):
    query = request.GET.get('q')
    dept_id = request.GET.get('department')
    status = request.GET.get('status')
    
    employees = Employee.objects.all().select_related('department')
    
    if query:
        employees = employees.filter(
            Q(full_name__icontains=query) | 
            Q(employee_code__icontains=query) |
            Q(user__email__icontains=query)
        )
    
    if dept_id:
        employees = employees.filter(department_id=dept_id)
        
    if status:
        employees = employees.filter(status=status)
        
    departments = Department.objects.all()
    
    return render(request, 'employees/list.html', {
        'employees': employees,
        'departments': departments,
        'current_status': status,
        'current_dept': dept_id,
        'current_query': query,
    })

@login_required
@role_required(['Admin', 'HR'])
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    attendance_logs = employee.attendance_logs.order_by('-date')[:30]
    return render(request, 'employees/detail.html', {
        'employee': employee,
        'attendance_logs': attendance_logs,
    })

@login_required
@role_required(['Admin', 'HR'])
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            return redirect('employees:detail', pk=employee.pk)
    else:
        form = EmployeeForm()
    return render(request, 'employees/form.html', {'form': form})

@login_required
@role_required(['Admin', 'HR'])
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employees:detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/form.html', {'form': form, 'edit_mode': True})
