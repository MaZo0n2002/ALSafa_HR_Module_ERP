from decimal import Decimal
import datetime
from django.db import models
from django.db.models import Sum, Max, Q
from django.core.exceptions import ValidationError
from employees.models import Employee


from accounts.models import Branch

class SystemConfiguration(models.Model):
    """Configuration rules per branch."""
    branch = models.OneToOneField(Branch, on_delete=models.CASCADE, related_name='configuration')
    working_days_per_month = models.IntegerField(default=22)
    shift_start_time = models.TimeField(default=datetime.time(9, 0))
    shift_end_time = models.TimeField(default=datetime.time(17, 0))
    overtime_rate_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    late_deduction_rate_per_minute = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    insurance_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.05)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.15)
    grace_period_minutes = models.IntegerField(default=15)

    class Meta:
        verbose_name_plural = "System Configuration"

    def __str__(self):
        return f"Config for {self.branch.name}"

    @classmethod
    def get_config(cls, branch=None):
        if branch:
            config = cls.objects.filter(branch=branch).first()
            if not config:
                # Create a specific config for this branch if missing, copying defaults
                config = cls.objects.create(branch=branch)
            return config
        # Fallback for global or missing branch
        return cls.objects.filter(branch__isnull=True).first() or cls.objects.filter(branch__name='Alexandria').first() or cls.objects.first()

class Loan(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_installment = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.remaining_balance = self.total_amount
        
        # Ensure monetary rules
        if self.remaining_balance <= 0:
            self.remaining_balance = Decimal('0.00')
            self.is_active = False

        self.total_amount = Decimal(self.total_amount).quantize(Decimal('0.00'))
        self.monthly_installment = Decimal(self.monthly_installment).quantize(Decimal('0.00'))
        self.remaining_balance = Decimal(self.remaining_balance).quantize(Decimal('0.00'))
        
        super().save(*args, **kwargs)

    def deduct_installment(self):
        """Called when payroll is generated to deduct the installment."""
        if self.is_active and self.remaining_balance > 0:
            deduction = min(self.monthly_installment, self.remaining_balance)
            self.remaining_balance -= deduction
            self.save()
            return deduction
        return Decimal('0.00')

    def __str__(self):
        return f"Loan: {self.employee} - {self.remaining_balance} remaining"


class Earning(models.Model):
    EARNING_TYPES = [
        ('Bonus', 'Performance Bonus'),
        ('Overtime', 'Overtime Pay'),
        ('Commission', 'Sales Commission'),
        ('Allowance', 'General Allowance'),
        ('Housing', 'Housing Allowance'),
        ('Transport', 'Transport Allowance'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='earnings')
    type = models.CharField(max_length=20, choices=EARNING_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=datetime.date.today)
    description = models.CharField(max_length=255, blank=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be positive.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type}: {self.amount} for {self.employee}"

class Deduction(models.Model):
    DEDUCTION_TYPES = [
        ('Absence', 'Absence Deduction'),
        ('Late', 'Late Coming'),
        ('Penalty', 'Disciplinary Penalty'),
        ('Insurance', 'Social Insurance'),
        ('Tax', 'Income Tax'),
        ('Loan', 'Loan Repayment'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='deductions')
    type = models.CharField(max_length=20, choices=DEDUCTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=datetime.date.today)
    description = models.CharField(max_length=255, blank=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be positive.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type}: {self.amount} from {self.employee}"


class Payslip(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Paid', 'Paid'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    month = models.IntegerField()
    year = models.IntegerField()
    
    # These fields are cached snapshots for record-keeping
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    
    # Automated Attendance-based values
    overtime_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    attendance_late_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    attendance_absence_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    loan_installment_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')

    def clean(self):
        if not self.employee.is_active:
            raise ValidationError("Cannot generate payroll for an inactive employee.")

    def save(self, *args, **kwargs):
        self.clean()
        config = SystemConfiguration.get_config(self.employee.branch)
        
        # 1. Base Salary
        base_salary = self.employee.basic_salary or Decimal('0.00')
        
        # 2. Calculate Manual Earnings
        manual_earnings_sum = Earning.objects.filter(
            employee=self.employee, 
            date__month=self.month, 
            date__year=self.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # 3. Calculate Attendance-based Earnings (Overtime)
        attendance_logs = self.employee.attendance_logs.filter(date__month=self.month, date__year=self.year)
        total_ot_hours = sum(log.overtime_hours for log in attendance_logs)
        self.overtime_earnings = Decimal(total_ot_hours) * config.overtime_rate_per_hour
        
        self.total_earnings = base_salary + manual_earnings_sum + self.overtime_earnings
        
        # 4. Calculate Manual Deductions
        manual_deductions_sum = Deduction.objects.filter(
            employee=self.employee, 
            date__month=self.month, 
            date__year=self.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # 5. Calculate Attendance-based Deductions (Late/Absence)
        total_late_minutes = sum(log.late_minutes for log in attendance_logs)
        self.attendance_late_deduction = Decimal(total_late_minutes) * config.late_deduction_rate_per_minute
        
        # Absence Deduction (Only if not exempt)
        self.attendance_absence_deduction = Decimal('0.00')
        if self.employee.requires_attendance_tracking:
            absent_days = attendance_logs.filter(status='Absent').count()
            # Calculate daily rate (Basic Salary / Working Days)
            daily_rate = base_salary / Decimal(config.working_days_per_month or 22)
            self.attendance_absence_deduction = Decimal(absent_days) * daily_rate

        # 6. Loan installments
        active_loans = self.employee.loans.filter(is_active=True)
        self.loan_installment_deduction = sum(min(loan.monthly_installment, loan.remaining_balance) for loan in active_loans)
        
        self.total_deductions = manual_deductions_sum + self.attendance_late_deduction + self.attendance_absence_deduction + Decimal(self.loan_installment_deduction)
        self.net_salary = max(Decimal('0.00'), self.total_earnings - self.total_deductions)

        # If marking as paid, process loans
        if self.status == 'Paid' and self.pk:
            old_slip = Payslip.objects.filter(pk=self.pk).first()
            if old_slip and old_slip.status != 'Paid':
                for loan in self.employee.loans.filter(is_active=True):
                    loan.deduct_installment()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payslip: {self.employee} - {self.month}/{self.year} | Net: {self.net_salary}"

# Signals to update Payslip when Earnings or Deductions change
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=Earning)
@receiver([post_save, post_delete], sender=Deduction)
def update_payslip_on_change(sender, instance, **kwargs):
    # Find the payslip for this employee, month, and year
    month = instance.date.month
    year = instance.date.year
    payslip = Payslip.objects.filter(employee=instance.employee, month=month, year=year).first()
    if payslip:
        print(f"DEBUG: Triggering recalculation for {instance.employee} - {month}/{year}")
        payslip.save() # This triggers the recalculation logic in Payslip.save()
