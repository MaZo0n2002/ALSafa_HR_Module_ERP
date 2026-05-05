from decimal import Decimal
import datetime
from django.db import models
from django.core.exceptions import ValidationError
from employees.models import Employee


class SystemConfiguration(models.Model):
    """Singleton model for global payroll rules."""
    working_days_per_month = models.IntegerField(default=22)
    shift_start_time = models.TimeField(default=datetime.time(9, 0))
    shift_end_time = models.TimeField(default=datetime.time(17, 0))
    overtime_rate_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    late_deduction_rate_per_minute = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    insurance_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.05, help_text="e.g., 0.05 for 5%")
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.15, help_text="e.g., 0.15 for 15%")

    class Meta:
        verbose_name_plural = "System Configuration"

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion

    @classmethod
    def get_config(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Global Payroll Rules"


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
        ('Bonus', 'Bonus'),
        ('Overtime', 'Overtime'),
        ('Allowance', 'Allowance'),
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
        ('Late', 'Late'),
        ('Loan', 'Loan'),
        ('Penalty', 'Penalty'),
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
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')

    def clean(self):
        if not self.employee.is_active:
            raise ValidationError("Cannot generate payroll for an inactive employee.")

    def save(self, *args, **kwargs):
        self.clean()
        
        # Calculate Earnings
        earnings = Earning.objects.filter(employee=self.employee, date__month=self.month, date__year=self.year)
        total_earnings = sum(e.amount for e in earnings)
        self.total_earnings = (self.employee.basic_salary or Decimal('0.00')) + Decimal(total_earnings)
        
        # Calculate Deductions
        deductions = Deduction.objects.filter(employee=self.employee, date__month=self.month, date__year=self.year)
        total_deductions = sum(d.amount for d in deductions)
        
        # Add dynamic deductions (Loan installments)
        active_loans = self.employee.loans.filter(is_active=True)
        loan_total = sum(min(loan.monthly_installment, loan.remaining_balance) for loan in active_loans)
        
        self.total_deductions = Decimal(total_deductions) + Decimal(loan_total)
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
