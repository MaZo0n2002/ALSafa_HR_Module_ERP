from django.core.management.base import BaseCommand
from zkteco.models import ZKTecoDevice
from zkteco.utils import sync_attendance_from_device

class Command(BaseCommand):
    help = 'Syncs attendance from all active ZKTeco biometric devices'

    def handle(self, *args, **options):
        devices = ZKTecoDevice.objects.filter(is_active=True)
        
        if not devices.exists():
            self.stdout.write(self.style.WARNING("No active ZKTeco devices found."))
            return

        for device in devices:
            self.stdout.write(f"Syncing device: {device.name} ({device.ip_address})...")
            success, message = sync_attendance_from_device(device.id)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f"Successfully synced {device.name}: {message}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to sync {device.name}: {message}"))
