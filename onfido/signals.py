# -*- coding: utf-8 -*-
"""
onfido signals.

Signals are fired when corresponding callbacks are received.

See https://documentation.onfido.com/#webhooks

"""
from django.dispatch import Signal

# fired after the status of a report /check is updated
# e.g. (obj, 'report.completed', 'pending', 'complete')
on_status_change = Signal(
    providing_args=['instance', 'event', 'status_before', 'status_after']
)

# 'complete' is the terminal state of both checks and reports, and as
# such it gets special treatment - it's the event that most people will
# be interested, so instead of having to filter out the on_status_change
# signal that results in completion, we have a dedicated signal.
on_completion = Signal(
    providing_args=['instance', 'completed_at']
)
