from django.db import models

class ZKTecoDevice(models.Model):
    name = models.CharField(max_length=100, default="Main Office Device")
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=4370)
    branch = models.ForeignKey('accounts.Branch', on_delete=models.CASCADE, related_name='zkteco_devices', null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    class Meta:
        verbose_name = "ZKTeco Device"
        verbose_name = "ZKTeco Devices"
