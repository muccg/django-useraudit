from django.conf.urls import include, url
from .views import reactivate_user

app_name = "useraudit"

urlpatterns = [
    url(r'reactivate/(?P<user_id>\d+)[/]?$', reactivate_user, name="reactivate_user"),
]
