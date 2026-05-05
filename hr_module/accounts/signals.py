from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from audit.models import AuditLog
from payroll.models import Payslip
from employees.models import Employee

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(user=user, action="User logged in successfully")

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    # we don't have the user object if it failed, but we log the attempt
    AuditLog.objects.create(action=f"Failed login attempt for {credentials.get('username')}")

@receiver(post_save, sender=Payslip)
def log_payslip_generation(sender, instance, created, **kwargs):
    # Using None for user since signals don't easily have access to the request object.
    # If generated via admin, we would need middleware. For now, we log the action.
    if created:
        AuditLog.objects.create(action=f"Payslip generated for {instance.employee} for {instance.month}/{instance.year}")
    elif instance.status == 'Paid':
        AuditLog.objects.create(action=f"Payslip marked as Paid for {instance.employee} for {instance.month}/{instance.year}")

@receiver(pre_save, sender=Employee)
def log_salary_changes(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Employee.objects.get(pk=instance.pk)
        if old_instance.basic_salary != instance.basic_salary:
            AuditLog.objects.create(
                user=instance.user, # Employee's user profile if available
                action=f"Base salary changed from {old_instance.basic_salary} to {instance.basic_salary} for {instance}"
            )
