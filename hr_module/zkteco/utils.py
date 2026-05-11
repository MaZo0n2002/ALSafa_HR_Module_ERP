# pyrefly: ignore [missing-import]
from zk import ZK, const
from datetime import datetime, date
from django.utils import timezone
from employees.models import Employee
from attendance.models import AttendanceLog
from .models import ZKTecoDevice

def sync_attendance_from_device(device_id):
    try:
        device_config = ZKTecoDevice.objects.get(id=device_id)
    except ZKTecoDevice.DoesNotExist:
        return False, "Device not found"

    zk = ZK(device_config.ip_address, port=device_config.port, timeout=5, password=0, force_udp=False, ommit_ping=True)
    conn = None
    
    try:
        conn = zk.connect()
        # conn.disable_device() 
        
        attendance = conn.get_attendance()
        total_records = len(attendance)
        
        if total_records == 0:
            return True, "Connected successfully, but no attendance logs were found on the device."
        
        # Group attendance by employee and date
        logs_by_day = {}
        for record in attendance:
            day = record.timestamp.date()
            # Ensure user_id is treated consistently (stripped string)
            zk_id = str(record.user_id).strip()
            key = (zk_id, day)
            
            if key not in logs_by_day:
                logs_by_day[key] = []
            logs_by_day[key].append(record.timestamp.time())

        # Now sync to AttendanceLog
        sync_count = 0
        skipped_count = 0
        branch_mismatch_count = 0
        
        for (zk_id, day), times in logs_by_day.items():
            # Try to match by zkteco_id (Integer in DB)
            try:
                numeric_id = int(zk_id)
                employee_qs = Employee.objects.filter(zkteco_id=numeric_id)
            except ValueError:
                employee_qs = Employee.objects.filter(zkteco_id=None) # Or handle non-numeric IDs if they exist

            employee = employee_qs.first()
            
            if not employee:
                skipped_count += 1
                continue

            if not employee.requires_attendance_tracking:
                # Silently skip exempt employees
                continue
            
            # Check branch if device has one
            if device_config.branch and employee.branch != device_config.branch:
                branch_mismatch_count += 1
                continue
            
            times.sort()
            first_punch = times[0]
            last_punch = times[-1] if len(times) > 1 else None
            
            log, created = AttendanceLog.objects.get_or_create(
                employee=employee,
                date=day
            )
            
            updated = False
            if not log.check_in or first_punch < log.check_in:
                log.check_in = first_punch
                updated = True
            
            if last_punch:
                if not log.check_out or last_punch > log.check_out:
                    log.check_out = last_punch
                    updated = True
            
            if updated or created:
                log.save()
                sync_count += 1

        # Post-Sync Pass: Ensure all active employees in this branch have a log for the days found
        distinct_days = {day for (zk_id, day) in logs_by_day.keys()}
        # If no logs found, at least sync for today
        if not distinct_days:
            distinct_days.add(date.today())

        # Get all active employees for this branch
        branch_employees = Employee.objects.filter(is_active=True)
        if device_config.branch:
            branch_employees = branch_employees.filter(branch=device_config.branch)

        for day in distinct_days:
            for employee in branch_employees:
                # Check if a log already exists (created by sync or manually)
                log, created = AttendanceLog.objects.get_or_create(
                    employee=employee,
                    date=day
                )
                if created:
                    # This employee had NO log from the terminal.
                    # AttendanceLog.save() will handle 'Absent' vs 'Present' based on exemption
                    log.save()

        device_config.last_sync = timezone.now()
        device_config.save()
        
        msg = f"Synchronization complete. Processed {len(logs_by_day)} attendance records. "
        msg += f"Updated or created {sync_count} records. "
        if skipped_count > 0:
            msg += f"{skipped_count} IDs were not found in staff directory. "
            
        return True, msg
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return False, f"Error: {str(e)}"
    finally:
        if conn:
            conn.disconnect()
