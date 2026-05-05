from django.db import models
from django.conf import settings

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Position(models.Model):
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')

    def __str__(self):
        return f"{self.title} - {self.department.name}"

class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True)
    employee_code = models.CharField(max_length=20, unique=True, help_text="Unique employee identifier")
    full_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, blank=True) # Keeping for backwards compatibility
    last_name = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    job_title = models.CharField(max_length=100, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fixed monthly base salary")
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('On Leave', 'On Leave'),
        ('Resigned', 'Resigned'),
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    join_date = models.DateField(null=True, blank=True)
    hire_date = models.DateField() # Original field
    is_active = models.BooleanField(default=True)
    zkteco_id = models.IntegerField(null=True, blank=True, help_text="User ID mapped from ZKTime biometric device")

    def __str__(self):
        return f"[{self.employee_code}] {self.full_name}"
