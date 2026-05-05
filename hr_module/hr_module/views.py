from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from employees.models import Employee
from attendance.models import AttendanceLog
from payroll.models import Payslip
from accounts.decorators import role_required

@login_required
@role_required(['Admin', 'HR'])
def dashboard(request):
    today = date.today()
    
    # Admin/Manager Stats
    total_employees = Employee.objects.filter(is_active=True).count()
    active_employees = Employee.objects.filter(status='Active').count()
    on_leave_employees = Employee.objects.filter(status='On Leave').count()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    pending_users = User.objects.filter(status='Pending').count()
    
    from leaves.models import LeaveRequest
    pending_leaves = LeaveRequest.objects.filter(status='Pending').count()
    
    today_attendance = AttendanceLog.objects.filter(date=today).exclude(status='Absent').count()
    total_payslips = Payslip.objects.filter(month=today.month, year=today.year).count()
    
    return render(request, 'dashboard.html', {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'on_leave_employees': on_leave_employees,
        'pending_users': pending_users,
        'pending_leaves': pending_leaves,
        'today_attendance': today_attendance,
        'total_payslips': total_payslips,
    })
