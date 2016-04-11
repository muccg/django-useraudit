from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib import admin
from useraudit import models as m


class LogAdmin(admin.ModelAdmin):
    model = m.Log

    search_fields = ['username']
    list_filter = ['timestamp']
    list_display = ('username', 'ip_address', 'forwarded_by', 'user_agent', 'timestamp')
    list_display_links = None


class LoginAttemptAdmin(admin.ModelAdmin):
    model = m.LoginAttempt
    
    list_display = ('username', 'count', 'timestamp', 'activate')
    list_display_links = None
    
    def activate(self, obj):
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get_by_natural_key(obj.username)
            if user.is_active:
                return "Active"
            activation_url = reverse("reactivate_user", args=[user.id,])
            return "<a href='%s'>Activate</a>" % activation_url
        except UserModel.DoesNotExist:
            return "N/A"
    
    activate.short_description = "Status"
    activate.allow_tags = True


admin.site.register(m.LoginLog, LogAdmin)
admin.site.register(m.FailedLoginLog, LogAdmin)
admin.site.register(m.LoginAttempt, LoginAttemptAdmin)