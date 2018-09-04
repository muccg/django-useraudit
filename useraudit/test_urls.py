from django.contrib import admin
from .views import test_request_available

try:
    from django.urls import include, path
    PRE_DJANGO_2 = False
except ImportError:
    from django.conf.urls import include, url
    PRE_DJANGO_2 = True


admin.autodiscover()

if PRE_DJANGO_2:
    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),
        url(r'test_request_available[/]?$', test_request_available),
    ]
else:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('test_request_available/', test_request_available),
    ]
