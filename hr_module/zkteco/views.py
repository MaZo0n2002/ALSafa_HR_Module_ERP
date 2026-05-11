from employees.models import Employee
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ZKTecoDevice
from .utils import sync_attendance_from_device

def device_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        ip = request.POST.get('ip_address')
        port = request.POST.get('port', 4370)
        
        if name and ip:
            device = ZKTecoDevice.objects.create(name=name, ip_address=ip, port=port)
            if request.user.branch:
                device.branch = request.user.branch
                device.save()
            messages.success(request, f"Device {name} added successfully.")
            return redirect('zkteco:device_list')
        else:
            messages.error(request, "Name and IP Address are required.")

    devices = ZKTecoDevice.objects.all()
    if request.user.branch:
        devices = devices.filter(branch=request.user.branch)
    return render(request, 'zkteco/device_list.html', {'devices': devices})

def sync_device(request, device_id):
    success, message = sync_attendance_from_device(device_id)
    if success:
        messages.success(request, message)
    else:
        messages.error(request, f"Sync failed: {message}")
    return redirect('zkteco:device_list')

def device_users(request, device_id):
    from zk import ZK
    try:
        device = ZKTecoDevice.objects.get(id=device_id)
        zk = ZK(device.ip_address, port=device.port, timeout=5)
        conn = None
        users = []
        try:
            conn = zk.connect()
            zk_users = conn.get_users()
            # Map ZKTeco IDs to ERP Employees
            erp_employees = {e.zkteco_id: e.full_name for e in Employee.objects.exclude(zkteco_id=None)}
            
            for u in zk_users:
                erp_name = erp_employees.get(int(u.user_id))
                users.append({
                    'uid': u.uid,
                    'user_id': u.user_id,
                    'name': u.name, # Name on Device
                    'erp_name': erp_name, # Name in ERP
                    'privilege': u.privilege,
                })
        finally:
            if conn:
                conn.disconnect()
        return render(request, 'zkteco/device_users.html', {'device': device, 'users': users})
    except Exception as e:
        messages.error(request, f"Could not fetch users: {str(e)}")
        return redirect('zkteco:device_list')

def link_user(request, device_id, user_id):
    try:
        device = ZKTecoDevice.objects.get(id=device_id)
    except ZKTecoDevice.DoesNotExist:
        messages.error(request, "Device not found.")
        return redirect('zkteco:device_list')

    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        new_name = request.POST.get('new_name')
        
        if employee_id:
            employee = Employee.objects.get(id=employee_id)
            employee.zkteco_id = user_id
            employee.save()
            messages.success(request, f"Linked {employee.full_name} to Biometric ID {user_id}")
        elif new_name:
            import datetime
            Employee.objects.create(
                full_name=new_name,
                zkteco_id=user_id,
                branch=device.branch,
                basic_salary=0,
                hire_date=datetime.date.today(),
                status='Active'
            )
            messages.success(request, f"Created and linked {new_name} to ID {user_id} in {device.branch.name if device.branch else 'Global'}")
            
        return redirect('zkteco:device_users', device_id=device_id)

    # Show employees from the DEVICE'S branch
    employees = Employee.objects.all().order_by('full_name')
    if device.branch:
        # Show employees in this branch OR employees with NO branch yet
        from django.db.models import Q
        employees = employees.filter(Q(branch=device.branch) | Q(branch__isnull=True))
        
    return render(request, 'zkteco/link_user.html', {
        'device_id': device_id,
        'user_id': user_id,
        'employees': employees,
        'device': device
    })
