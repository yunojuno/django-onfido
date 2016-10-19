# -*- coding: utf-8 -*-
"""onfido urls."""
from django.conf.urls import url

from onfido.views import status_update

urlpatterns = [
    url(r'^webhook/$', status_update, name='status_update'),
]
