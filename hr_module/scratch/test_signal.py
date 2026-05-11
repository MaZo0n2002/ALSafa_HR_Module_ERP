import os
import django
import sys

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from employees.models import Employee
from attendance.models import AttendanceLog
import datetime

def test_exemption_propagation():
    print("--- Biometric Exemption Propagation Test ---")
    
    # 1. Create or get a test employee
    emp_code = f"T-{datetime.datetime.now().strftime('%M%S')}"
    emp = Employee.objects.create(
        full_name="Signal Test Employee",
        employee_code=emp_code,
        basic_salary=5000,
        hire_date=datetime.date.today(),
        requires_attendance_tracking=True
    )
    
    # 2. Create an ABSENT log for today
    today = datetime.date.today()
    log = AttendanceLog.objects.create(
        employee=emp,
        date=today,
        status='Absent'
    )
    
    print(f"Employee Created: {emp.full_name} ({emp_code})")
    print(f"Initial Attendance Status: {log.status}")
    
    # 3. Change employee to EXEMPT
    print("ACTION: Setting employee to EXEMPT (requires_attendance_tracking = False)...")
    emp.requires_attendance_tracking = False
    emp.save()
    
    # 4. Check if log status updated
    log.refresh_from_db()
    print(f"Updated Attendance Status: {log.status}")
    
    if log.status == 'Present':
        print("\n[SUCCESS] Signal propagated changes to attendance logs.")
        print("Integration verified: Exempting a user fixes their logs automatically.")
    else:
        print("\n[FAILURE] Signal did not update attendance logs.")
        print(f"Log status is still {log.status}")

if __name__ == "__main__":
    test_exemption_propagation()
