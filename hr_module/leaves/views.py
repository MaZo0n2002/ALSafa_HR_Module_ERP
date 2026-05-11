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
    leaves = LeaveRequest.objects.all().select_related('employee').order_by('-applied_on')
    if request.user.branch:
        leaves = leaves.filter(employee__branch=request.user.branch)
    return render(request, 'leaves/list.html', {'leaves': leaves})

@login_required
@role_required(['Admin', 'HR'])
def leave_request(request):
    # This view now allows HR to submit leave on behalf of an employee
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        employee_id = request.POST.get('employee_id')
        if form.is_valid() and employee_id:
            # Security: ensure the employee belongs to the user's branch
            employee_qs = Employee.objects.all()
            if request.user.branch:
                employee_qs = employee_qs.filter(branch=request.user.branch)
            employee = get_object_or_404(employee_qs, id=employee_id)
            
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, f"Leave recorded for {employee.full_name}.")
            return redirect('leaves:list')
    else:
        form = LeaveRequestForm()
    
    employees = Employee.objects.all()
    if request.user.branch:
        employees = employees.filter(branch=request.user.branch)
        
    return render(request, 'leaves/form.html', {'form': form, 'employees': employees})

@login_required
@role_required(['Admin', 'HR', 'Manager'])
def leave_approve(request, pk):
    queryset = LeaveRequest.objects.all()
    if request.user.branch:
        queryset = queryset.filter(employee__branch=request.user.branch)
    leave = get_object_or_404(queryset, pk=pk)
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
    queryset = LeaveRequest.objects.all()
    if request.user.branch:
        queryset = queryset.filter(employee__branch=request.user.branch)
    leave = get_object_or_404(queryset, pk=pk)
    leave.status = 'Rejected'
    leave.save()
    messages.success(request, f"Leave request for {leave.employee.full_name} rejected.")
    return redirect('leaves:list')

@login_required
@role_required(['Admin', 'HR'])
def import_leaves(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        import pandas as pd
        from django.http import HttpResponse
        file = request.FILES['excel_file']
        
        try:
            df = pd.read_excel(file)
            required_cols = ['employee_code', 'leave_type', 'start_date', 'end_date']
            if not all(col in df.columns for col in required_cols):
                messages.error(request, f"Missing columns. Required: {', '.join(required_cols)}")
                return redirect('leaves:list')

            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    emp_code = str(row['employee_code']).strip()
                    l_type = str(row['leave_type']).strip().capitalize()
                    s_date = row['start_date']
                    e_date = row['end_date']
                    reason = str(row.get('reason', 'Bulk Import')).strip()
                    
                    employee = Employee.objects.filter(employee_code=emp_code).first()
                    if not employee:
                        error_count += 1
                        continue
                    
                    # Ensure branch permission
                    if request.user.branch and employee.branch != request.user.branch:
                        error_count += 1
                        continue

                    LeaveRequest.objects.create(
                        employee=employee,
                        leave_type=l_type if l_type in dict(LeaveRequest.LEAVE_TYPES) else 'Other',
                        start_date=s_date,
                        end_date=e_date,
                        reason=reason,
                        status='Approved' # Auto-approve bulk imports
                    )
                    
                    # Update employee status
                    employee.status = 'On Leave'
                    employee.save()
                    
                    success_count += 1
                except Exception:
                    error_count += 1
                    
            messages.success(request, f"Import complete: {success_count} success, {error_count} errors.")
            return redirect('leaves:list')
            
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return render(request, 'leaves/import.html')

@login_required
@role_required(['Admin', 'HR'])
def download_leave_template(request):
    import pandas as pd
    from django.http import HttpResponse
    df = pd.DataFrame(columns=['employee_code', 'leave_type', 'start_date', 'end_date', 'reason'])
    df.loc[0] = ['EMP001', 'Annual', '2026-05-15', '2026-05-20', 'Family Vacation']
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=leaves_import_template.xlsx'
    
    df.to_excel(response, index=False)
    return response
