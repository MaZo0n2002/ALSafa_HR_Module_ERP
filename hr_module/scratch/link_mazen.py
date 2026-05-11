from employees.models import Employee

mazen = Employee.objects.filter(full_name__icontains='mazen').first()
if mazen:
    mazen.zkteco_id = 44
    mazen.save()
    print(f"Linked {mazen.full_name} to ID 44")
else:
    print("Mazen not found")
