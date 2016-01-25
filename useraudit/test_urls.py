from django.conf.urls import include, url
from django.contrib import admin
from .views import test_request_available
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'test_request_available[/]?$', test_request_available),
]
