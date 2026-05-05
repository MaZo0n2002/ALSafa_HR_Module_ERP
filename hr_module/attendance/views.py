from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AttendanceLog
from accounts.decorators import role_required

@login_required
@role_required(['Admin', 'HR'])
def attendance_list(request):
    attendance = AttendanceLog.objects.select_related('employee').order_by('-date')[:100]
    return render(request, 'attendance/list.html', {'attendance': attendance})
