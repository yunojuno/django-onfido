from django.contrib import admin
from django.urls import include, path

import onfido.urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("onfido/", include(onfido.urls)),
]
