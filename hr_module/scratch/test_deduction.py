import os
import django
import sys
from decimal import Decimal

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from employees.models import Employee
from payroll.models import Payslip, Deduction
import datetime

def test_deduction_calculation():
    print("--- Deduction Calculation Test ---")
    
    # 1. Get or create a test employee
    emp, _ = Employee.objects.get_or_create(
        full_name="Deduction Test Emp",
        defaults={
            'employee_code': 'DED-TEST',
            'basic_salary': 5000,
            'hire_date': datetime.date.today(),
            'requires_attendance_tracking': False
        }
    )
    
    # 2. Ensure a payslip exists for the current month
    today = datetime.date.today()
    payslip, created = Payslip.objects.get_or_create(
        employee=emp,
        month=today.month,
        year=today.year,
        defaults={'status': 'Draft'}
    )
    
    # Recalculate to be sure
    payslip.save()
    print(f"Initial Payslip Deductions: {payslip.total_deductions}")
    
    # 3. Add a manual deduction
    print(f"ACTION: Adding a 100.00 penalty for {today}...")
    deduction = Deduction.objects.create(
        employee=emp,
        type='Penalty',
        amount=Decimal('100.00'),
        date=today
    )
    
    # 4. Check if payslip updated (via signal)
    payslip.refresh_from_db()
    print(f"Updated Payslip Deductions: {payslip.total_deductions}")
    
    if payslip.total_deductions >= 100:
        print("\n[SUCCESS] Deduction was correctly calculated in the payslip.")
    else:
        print("\n[FAILURE] Deduction was NOT added to the payslip.")
        
    # Cleanup
    # deduction.delete()
    # payslip.delete()
    # emp.delete()

if __name__ == "__main__":
    test_deduction_calculation()
