from employees.models import Department, Employee

# 1. Find all unique names
names = set(Department.objects.values_list('name', flat=True))

for name in names:
    depts = list(Department.objects.filter(name=name))
    if len(depts) > 1:
        keep = depts[0]
        to_delete = depts[1:]
        
        # Move employees from duplicates to the one we keep
        for d in to_delete:
            Employee.objects.filter(department=d).update(department=keep)
            d.delete()
        print(f"Merged {len(to_delete) + 1} '{name}' departments into one.")
    else:
        print(f"Only one '{name}' department exists, no merge needed.")
