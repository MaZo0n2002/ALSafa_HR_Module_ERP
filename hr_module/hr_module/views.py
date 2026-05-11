from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from employees.models import Employee
from attendance.models import AttendanceLog
from payroll.models import Payslip
from leaves.models import LeaveRequest
from accounts.decorators import role_required

User = get_user_model()

@login_required
@role_required(['Admin', 'HR'])
def dashboard(request):
    today = date.today()
    
    # Base Querysets (Filtered by branch)
    emp_qs = Employee.objects.all()
    user_qs = User.objects.all()
    leave_qs = LeaveRequest.objects.all()
    att_qs = AttendanceLog.objects.all()
    pay_qs = Payslip.objects.all()
    
    if request.user.branch:
        emp_qs = emp_qs.filter(branch=request.user.branch)
        user_qs = user_qs.filter(branch=request.user.branch)
        leave_qs = leave_qs.filter(employee__branch=request.user.branch)
        att_qs = att_qs.filter(employee__branch=request.user.branch)
        pay_qs = pay_qs.filter(employee__branch=request.user.branch)

    # Admin/Manager Stats
    total_employees = emp_qs.filter(is_active=True).count()
    active_employees = emp_qs.filter(status='Active').count()
    on_leave_employees = emp_qs.filter(status='On Leave').count()
    pending_users = user_qs.filter(status='Pending').count()
    pending_leaves = leave_qs.filter(status='Pending').count()
    today_attendance = att_qs.filter(date=today).exclude(status='Absent').count()
    total_payslips = pay_qs.filter(month=today.month, year=today.year).count()
    
    return render(request, 'dashboard.html', {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'on_leave_employees': on_leave_employees,
        'pending_users': pending_users,
        'pending_leaves': pending_leaves,
        'today_attendance': today_attendance,
        'total_payslips': total_payslips,
    })
