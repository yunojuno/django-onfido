from django.contrib import admin
from django.urls import include, path
from django.views import debug

import onfido.urls

urlpatterns = [
    path("", debug.default_urlconf),
    path("admin/", admin.site.urls),
    path("onfido/", include(onfido.urls)),
]
