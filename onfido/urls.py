# -*- coding: utf-8 -*-
"""onfido urls."""
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'onfido.views',
    url(r'^webhook/$', 'status_update', name="status_update"),
)
