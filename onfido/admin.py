# -*- coding: utf-8 -*-
import simplejson as json  # simplejson supports Decimal

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from .models import (
    Applicant,
    Check,
    Report,
    Event
)


class RawMixin(object):

    """Admin mixin used to pprint raw JSON fields."""

    def _raw(self, obj):
        """
        Return an indented HTML pretty-print version of JSON.

        Take the event_payload JSON, indent it, order the keys and then
        present it as a <code> block. That's about as good as we can get
        until someone builds a custom syntax function.

        """
        pretty = json.dumps(
            obj.raw,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )
        html = pretty.replace(" ", "&nbsp;").replace("\n", "<br>")
        return mark_safe("<code>{}</code>".format(html))
    _raw.short_description = _("Raw (from API)")


class ApplicantAdmin(RawMixin, admin.ModelAdmin):

    """Admin model for Applicant objects."""

    list_display = ('user', 'created_at')
    list_filter = ('created_at',)
    ordering = ('user__first_name', 'user__last_name')
    readonly_fields = ('onfido_id', 'user', 'created_at', '_raw')
    raw_id_fields = ('user',)
    exclude = ('raw',)

admin.site.register(Applicant, ApplicantAdmin)


class CheckAdmin(RawMixin, admin.ModelAdmin):

    """Admin model for Check objects."""

    list_display = (
        'applicant', 'check_type', 'status',
        'result', 'created_at', 'updated_at'
    )
    readonly_fields = (
        'onfido_id', 'user', 'created_at', 'applicant', 'check_type',
        'status', 'result', 'updated_at', '_raw'
    )
    list_filter = ('check_type', 'created_at', 'status')
    raw_id_fields = ('applicant', 'user')
    exclude = ('raw',)

admin.site.register(Check, CheckAdmin)


class ReportAdmin(RawMixin, admin.ModelAdmin):

    """Admin model for Report objects."""

    list_display = (
        'onfido_check', 'report_type', 'status',
        'result', 'created_at', 'updated_at'
    )
    readonly_fields = (
        'onfido_id', 'user', 'onfido_check', 'report_type',
        'status', 'result', 'created_at', 'updated_at', '_raw'
    )
    list_filter = ('created_at', 'report_type', 'status')
    raw_id_fields = ('onfido_check', 'user')
    exclude = ('raw',)

admin.site.register(Report, ReportAdmin)


class EventAdmin(RawMixin, admin.ModelAdmin):

    """Admin model for Event objects."""

    list_display = (
        'resource_id', 'resource_type', 'action', 'status', 'completed_at'
    )
    list_filter = (
        'action', 'resource_type', 'completed_at'
    )
    readonly_fields = (
        'resource_id', 'resource_type', 'action', 'status', 'completed_at', '_raw'
    )
    exclude = ('raw',)

admin.site.register(Event, EventAdmin)
