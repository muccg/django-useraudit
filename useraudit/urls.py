from django.urls import re_path
from .views import reactivate_user

app_name = "useraudit"

urlpatterns = [
    re_path(r'reactivate/(?P<user_id>\d+)[/]?$', reactivate_user, name="reactivate_user"),
]
