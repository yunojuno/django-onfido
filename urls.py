from django.contrib import admin
try:
    from django.urls import re_path, include
except ImportError:
    from django.conf.urls import url as re_path
    from django.conf.urls import include

import onfido.urls

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^onfido/', include(onfido.urls)),
]
