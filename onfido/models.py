# -*- coding: utf-8 -*-
import datetime
import logging

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext as _

from .api import get, post, url as format_url
from .db.fields import JSONField
from .signals import on_status_change, on_completion

logger = logging.getLogger(__name__)


class BaseModel(models.Model):

    """Base model used to set timestamps."""

    id = models.CharField(
        primary_key=True,
        max_length=40,
        help_text=_("The id returned from the Onfido API."),
    )
    created_at = models.DateTimeField(
        help_text=_("The timestamp returned from the Onfido API.")
    )
    raw = JSONField(
        help_text=_("The raw JSON returned from the API.")
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Save object and return self (for chaining methods)."""
        super(BaseModel, self).save(*args, **kwargs)
        return self

    @property
    def api_get_path(self):
        """Return relative API path that points to the GET endpoint."""
        raise NotImplementedError()

    def parse_raw(self):
        """Parses the raw value out into other properties."""
        self.id = self.raw['id']
        self.created_at = datetime.datetime.strptime(
            self.raw['created_at'],
            '%Y-%m-%dT%H:%M:%SZ'
        )
        return self

    def fetch(self):
        """Fetch latest version from Api and update local data."""
        self.raw = get(format_url(self.api_get_path))
        return self

    def pull(self):
        """Fetch and parse the remote data."""
        return self.fetch().parse_raw().save()

class BaseStatusModel(BaseModel):

    """Base class for models with a status and result field."""

    status = models.CharField(
        max_length=20,
        default='unknown',
        help_text=_("The current state of the check / report (from API).")
    )
    result = models.CharField(
        max_length=20,
        help_text=_("The final result of the check / reports (from API)."),
        default='unknown'
    )
    updated_at = models.DateTimeField(
        blank=True, null=True,
        help_text=_("The timestamp of the most recent status change.")
    )

    class Meta:
        abstract = True

    def update_status(self, event, new_status, timestamp):
        """
        Update the status field of the object and fire signal(s).

        When the app receives an event callback from Onfido, we update
        the status of the relevant Check/Report, and then fire the
        signals that allow external apps to hook in to this event.

        If the update is a change to 'complete', then we fire a second
        signal - 'complete' is the terminal state change, and therefore
        of most interest to clients - typically the on_status_update
        signal would be registered for logging a complete history of
        changes, whereas the on_completion signal would be used to do
        something more useful - updating the status of the user, sending
        them an email etc.

        Args:
            event: string, the name of the event, e.g. 'report.completed'
            new_status: string, the new status, e.g. 'complete'
            timestamp: DateTime, from the callback `completed_at` value

        Returns the updated object.

        """
        # swap statuses around so we record old / new
        self.status, old_status = new_status, self.status
        self.updated_at = timestamp
        self.save()
        on_status_change.send(
            self.__class__,
            instance=self,
            status_before=old_status,
            status_after=new_status
        )
        if new_status == 'complete':
            on_completion.send(self.__class__, instance=self)
        return self

    def parse_raw(self):
        """Parses the raw value out into other properties."""
        super(BaseStatusModel, self).parse_raw()
        self.result=self.raw['result']
        self.status=self.raw['status']
        return self


class ApplicantManager(models.Manager):

    """Custom Applicant queryset."""

    def create_applicant(self, user):
        """Create a new applicant in Onfido from a user."""
        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
        response = post(format_url(Applicant.POST), data)
        logger.debug(response)
        return Applicant(user=user, raw=response).parse_raw().save()


class Applicant(BaseModel):

    """An Onfido applicant record."""

    GET = 'applicants/{}'
    POST = 'applicants'

    user = models.ForeignKey(
        User,
        help_text=_("Django user that maps to this applicant.")
    )

    objects = ApplicantManager()

    def __unicode__(self):
        return self.user.get_full_name() or self.user.username

    def __repr__(self):
        return u"<Applicant id=%s user='%s'>" % (
            self.id, self.user.username
        )

    @property
    def api_get_path(self):
        return Applicant.GET.format(self.id)


def create_check(
    applicant, check_type, reports,
    suppress_form_emails=True,
    redirect_uri=None
):
    """
    Create a new Check (and child Reports).

    Args:
        applicant: Applicant for whom the checks are being made.
        check_type: string, currently only 'standard' is supported.
        reports: list of strings, each of which is a valid report type.

    Kwargs:
        suppress_form_emails: bool, if True then suppress the email the Onfido
            itself would normally send when a check is initiated. Defaults to
            True.
        redirect_uri: string, a url to which to direct the user _after_ they
            have submitted all the information requested.

    Returns a new Check object, and creates the child Report objects.

    """
    data = {
        "type": check_type,
        "suppress_form_emails": suppress_form_emails,
        "reports": [{'name': r for r in reports}],
        "redirect_uri": redirect_uri
    }
    response = post(format_url(Applicant.POST), data)
    logger.debug(response)
    return Check(applicant=applicant, raw=response).parse_raw().save()


class Check(BaseStatusModel):

    """The state of an individual check made against an Applicant."""

    GET = 'applicants/{}/checks/{}'
    POST = 'applicants/{}/checks'

    CHECK_TYPE_CHOICES = (
        ('express', 'Express check'),
        ('standard', 'Standard check')
    )
    # DEPRECATED, pls keep for reference
    CHECK_STATUS_CHOICES = (
        ('unknown', 'Unknown'),
        ('in_progress', 'In progress'),
        ('awaiting_applicant', 'Awaiting applicant'),
        ('complete', 'Complete'),
        ('withdrawn', 'Withdrawn'),
        ('paused', 'Paused'),
        ('reopened', 'Reopened'),
    )
    # DEPRECATED, pls keep for reference
    CHECK_RESULT_CHOICES = (
        ('clear', 'Clear'),
        ('consider', 'Consider')
    )
    user = models.ForeignKey(
        User,
        help_text=_("The Django user (denormalised from Applicant to make navigation easier)."),  # noqa
        related_name='onfido_checks'
    )
    applicant = models.ForeignKey(
        Applicant,
        help_text=_("The applicant for whom the check is being made."),
        related_name='checks'
    )
    check_type = models.CharField(
        max_length=10,
        choices=CHECK_TYPE_CHOICES,
        help_text=_("See https://documentation.onfido.com/#check-types")
    )

    def __unicode__(self):
        return (
            u"%s for %s" % (
                self.get_check_type_display().capitalize(),
                self.user.get_full_name() or self.user.username
            )
        )

    def __repr__(self):
        return (
            u"<Check id=%s type='%s' user='%s'>" % (
                self.id,
                self.check_type,
                self.user
            )
        )

    @property
    def api_get_path(self):
        return Check.GET.format(self.applicant.id, self.id)

    def parse_raw(self):
        """Parses the raw value out into other properties."""
        super(Check, self).parse_raw()
        self.check_type=self.raw['type']
        return self


class Report(BaseStatusModel):

    """Specific reports associated with a Check."""

    REPORT_TYPE_CHOICES = (
        ('unknown', '-'),
        ('identity', 'Identity report'),
        ('document', 'Document report'),
        ('street_level', 'Street level report'),
        ('facial_similarity', 'Facial similarity report'),
    )
    # DEPRECATED, pls keep for reference
    REPORT_STATUS_CHOICES = (
        ('unknown', 'Unknown'),
        ('awaiting_data', 'Awaiting data'),
        ('awaiting_approval', 'Awaiting approval'),
        ('complete', 'Complete'),
        ('withdrawn', 'Withdrawn'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    )
    # DEPRECATED, pls keep for reference
    REPORT_RESULT_CHOICES = (
        ('unknown', 'Unknown'),
        ('clear', 'Clear'),
        ('consider', 'Consider'),
        ('unidentified', 'Unidentified'),
    )
    user = models.ForeignKey(
        User,
        help_text=_("The Django user (denormalised from Applicant to make navigation easier)."),  # noqa
        related_name='onfido_reports'
    )
    onfido_check = models.ForeignKey(
        Check,
        help_text=_("Check to which this report is attached."),
        related_name='reports'
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        help_text=_("The name of the report - see https://documentation.onfido.com/#reports")
    )

    def __unicode__(self):
        return (
            u"%s for %s" % (
                self.get_report_type_display().capitalize(),
                self.user.get_full_name() or self.user.username
            )
        )

    def __repr__(self):
        return (
            u'<Report id=%s type=%s user=%s>' % (
                self.id,
                self.report_type,
                self.user
            )
        )

    @property
    def api_get_path(self):
        return 'checks/{}/reports/{}'.format(self.onfido_check.id, self.id)

    def parse_raw(self):
        """Parses the raw value out into other properties."""
        super(Report, self).parse_raw()
        self.report_type=self.raw['name']
        return self
