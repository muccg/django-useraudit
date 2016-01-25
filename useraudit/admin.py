from django.contrib import admin
from useraudit import models as m


class LogAdmin(admin.ModelAdmin):
    model = m.Log

    search_fields = ['username']
    list_filter = ['timestamp']
    list_display = ('username', 'ip_address', 'forwarded_by', 'user_agent', 'timestamp')
    list_display_links = None


admin.site.register(m.LoginLog, LogAdmin)
admin.site.register(m.FailedLoginLog, LogAdmin)
