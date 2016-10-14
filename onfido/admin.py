# -*- coding: utf-8 -*-
import simplejson as json  # simplejson supports Decimal

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from .models import Applicant, Check, Report


def pprint(data):
    """
    Return an indented HTML pretty-print version of JSON.

    Take the event_payload JSON, indent it, order the keys and then
    present it as a <code> block. That's about as good as we can get
    until someone builds a custom syntax function.

    """
    pretty = json.dumps(
        data,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    )
    return mark_safe("<code>%s</code>" % pretty.replace(" ", "&nbsp;"))


class ApplicantAdmin(admin.ModelAdmin):

    """Admin model for Applicant objects."""

    list_display = ('id', 'user', 'created_at')
    list_filter = ('created_at',)
    ordering = ('user__first_name', 'user__last_name')
    readonly_fields = ('id', 'created_at', '_raw')
    raw_id_fields = ('user',)
    exclude = ('raw',)

    def _raw(self, obj):
        """Return pprint version of the raw field."""
        return pprint(obj.raw)
    _raw.short_description = _("Raw")

admin.site.register(Applicant, ApplicantAdmin)


class CheckAdmin(admin.ModelAdmin):

    """Admin model for Check objects."""

    list_display = ('id', 'applicant', 'check_type', 'created_at')
    list_filter = ('check_type', 'created_at',)
    readonly_fields = ('created_at', 'id')
    raw_id_fields = ('applicant',)

admin.site.register(Check, CheckAdmin)


class ReportAdmin(admin.ModelAdmin):

    """Admin model for Report objects."""

    list_display = ('onfido_check', 'report_type', 'created_at')
    list_filter = ('created_at', 'report_type')
    readonly_fields = ('created_at', 'id')
    raw_id_fields = ('onfido_check',)

admin.site.register(Report, ReportAdmin)
