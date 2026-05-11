from employees.models import Employee
from accounts.models import Branch

branch = Branch.objects.get(id=1) # Alexandria
employees_to_add = [
    (2, "Nora"),
    (3, "Mahmoud"),
    (4, "Daliaa"),
    (20, "Ramadan Sayed"),
    (22, "Omar Ali"),
    (36, "Mohamed Sayed"),
    (37, "Adham Mostafa"),
    (38, "Mayada"),
    (42, "Mohamed Elgzar"),
]

for zk_id, name in employees_to_add:
    emp, created = Employee.objects.get_or_create(
        zkteco_id=zk_id,
        defaults={
            'full_name': name,
            'branch': branch,
            'basic_salary': 0,
            'hire_date': '2026-01-01'
        }
    )
    if created:
        print(f"Created {name} (ID {zk_id})")
    else:
        print(f"{name} already exists")
