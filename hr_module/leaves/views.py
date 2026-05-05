from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from .models import LeaveRequest
from .forms import LeaveRequestForm
from employees.models import Employee

@login_required
@role_required(['Admin', 'HR'])
def leave_list(request):
    leaves = LeaveRequest.objects.all().order_by('-applied_on')
    return render(request, 'leaves/list.html', {'leaves': leaves})

@login_required
@role_required(['Admin', 'HR'])
def leave_request(request):
    # This view now allows HR to submit leave on behalf of an employee
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        employee_id = request.POST.get('employee_id')
        if form.is_valid() and employee_id:
            employee = get_object_or_404(Employee, id=employee_id)
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, f"Leave recorded for {employee.full_name}.")
            return redirect('leaves:list')
    else:
        form = LeaveRequestForm()
    employees = Employee.objects.all()
    return render(request, 'leaves/form.html', {'form': form, 'employees': employees})

@login_required
@role_required(['Admin', 'HR', 'Manager'])
def leave_approve(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'Approved'
    leave.save()
    
    # Update employee status if needed
    employee = leave.employee
    employee.status = 'On Leave'
    employee.save()
    
    messages.success(request, f"Leave request for {employee.full_name} approved.")
    return redirect('leaves:list')

@login_required
@role_required(['Admin', 'HR', 'Manager'])
def leave_reject(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'Rejected'
    leave.save()
    messages.success(request, f"Leave request for {leave.employee.full_name} rejected.")
    return redirect('leaves:list')
