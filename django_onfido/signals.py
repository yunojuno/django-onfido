# -*- coding: utf-8 -*-
"""
django_onfido signals.

Signals are fired when corresponding callbacks are received.

See https://documentation.onfido.com/#webhooks

"""
from django.dispatch import Signal

report_completed = Signal(providing_args=['instance'])
report_withdrawn = Signal(providing_args=['instance'])
check_started = Signal(providing_args=['instance'])
check_completed = Signal(providing_args=['instance'])
