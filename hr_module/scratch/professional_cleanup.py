from employees.models import Department, Employee

def merge(old_names, new_name):
    target, _ = Department.objects.get_or_create(name=new_name)
    for old in old_names:
        if old != new_name:
            depts = Department.objects.filter(name__iexact=old)
            for d in depts:
                Employee.objects.filter(department=d).update(department=target)
                d.delete()
                print(f"Merged '{old}' into '{new_name}'")

# Execute merges
merge(['IT', 'IT department', 'IT Department'], 'Information Technology (IT)')
merge(['HR', 'Human Resources', 'Human Resourses'], 'Human Resources (HR)')
merge(['Managers'], 'Management')
merge(['Others'], 'Other')

# Final check for any empty or redundant ones
for dept in Department.objects.all():
    if not Employee.objects.filter(department=dept).exists():
        # Keep it if it's one of our core ones, otherwise remove if it looks like junk
        if len(dept.name) < 3:
            dept.delete()
            print(f"Deleted junk department: {dept.name}")
