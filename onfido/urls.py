from django.urls import path

from .views import status_update

app_name = "onfido"

urlpatterns = [
    path("webhook/", status_update, name="status_update"),
]
