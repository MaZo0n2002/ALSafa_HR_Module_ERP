from django.contrib import admin
from .models import ZKTecoDevice

@admin.register(ZKTecoDevice)
class ZKTecoDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'port', 'last_sync', 'is_active')
    list_editable = ('is_active',)
