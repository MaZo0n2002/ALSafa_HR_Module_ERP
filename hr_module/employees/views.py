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
    branch_id = request.GET.get('branch')
    dept_id = request.GET.get('department')
    status = request.GET.get('status')
    
    employees = Employee.objects.all().select_related('department', 'branch')
    
    # Branch Filtering Logic
    if request.user.branch:
        selected_branch_id = request.user.branch.id
        employees = employees.filter(branch=request.user.branch)
    else:
        selected_branch_id = branch_id
        if branch_id:
            employees = employees.filter(branch_id=branch_id)
        
    if query:
        employees = employees.filter(
            Q(full_name__icontains=query) | 
            Q(employee_code__icontains=query) |
            Q(user__email__icontains=query)
        )
    
    # Department Filtering (Shared across branches)
    departments = Department.objects.all()
        
    if dept_id:
        employees = employees.filter(department_id=dept_id)
        
    if status:
        employees = employees.filter(status=status)
    
    from accounts.models import Branch
    branches = Branch.objects.all()
    
    return render(request, 'employees/list.html', {
        'employees': employees,
        'departments': departments,
        'branches': branches,
        'current_branch': branch_id,
        'current_status': status,
        'current_dept': dept_id,
        'current_query': query,
    })

@login_required
@role_required(['Admin', 'HR'])
def employee_detail(request, pk):
    queryset = Employee.objects.all()
    if request.user.branch:
        queryset = queryset.filter(branch=request.user.branch)
    employee = get_object_or_404(queryset, pk=pk)
    attendance_logs = employee.attendance_logs.order_by('-date')[:30]
    return render(request, 'employees/detail.html', {
        'employee': employee,
        'attendance_logs': attendance_logs,
    })

@login_required
@role_required(['Admin', 'HR'])
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, user=request.user)
        if form.is_valid():
            employee = form.save(commit=False)
            if request.user.branch and not employee.branch:
                employee.branch = request.user.branch
            employee.save()
            return redirect('employees:detail', pk=employee.pk)
    else:
        form = EmployeeForm(user=request.user)
    return render(request, 'employees/form.html', {'form': form})

@login_required
@role_required(['Admin', 'HR'])
def employee_edit(request, pk):
    queryset = Employee.objects.all()
    if request.user.branch:
        queryset = queryset.filter(branch=request.user.branch)
    employee = get_object_or_404(queryset, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('employees:detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee, user=request.user)
    return render(request, 'employees/form.html', {'form': form, 'edit_mode': True})
