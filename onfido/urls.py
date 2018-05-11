try:
    from django.urls import re_path, include
except ImportError:
    from django.conf.urls import url as re_path, include

from .views import status_update

app_name = 'onfido'

urlpatterns = [
    re_path(r'^webhook/$', status_update, name='status_update'),
]
