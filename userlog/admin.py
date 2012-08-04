from django.contrib import admin

from userlog import models as m

class LogAdmin(admin.ModelAdmin):
    model = m.Log

    search_fields = ['username']
    list_filter = ['timestamp']
    list_display = ('username', 'ip_address', 'user_agent', 'timestamp')


    # this disable the edit links. No supported way of doing it.
    def __init__(self, *args, **kwargs):
        admin.ModelAdmin.__init__(self, *args, **kwargs)
        self.list_display_links = (None, )

admin.site.register(m.LoginLog, LogAdmin)
admin.site.register(m.FailedLoginLog, LogAdmin)

