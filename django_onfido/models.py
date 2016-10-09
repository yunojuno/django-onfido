# -*- coding: utf-8 -*-
"""django_onfido models."""
import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

# from onfido import Api

from django_onfido.api import get, post, url as format_url
from django_onfido.db.fields import JSONField
# from django_onfido.settings import ONFIDO_API_KEY

# client = Api(ONFIDO_API_KEY)
logger = logging.getLogger(__name__)


class BaseModel(models.Model):

    """Base model used to set timestamps."""

    id = models.CharField(
        primary_key=True,
        max_length=40,
        help_text=_("The id returned from the Onfido API.")
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


class ApplicantQuerySet(models.query.QuerySet):

    """Custom Applicant queryset."""

    def create(self, user):
        """Create a new applicant in Onfido from a user."""
        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
        response = post(format_url(Applicant.POST), data)
        logger.debug(response)
        applicant = Applicant(
            id=response['id'],
            user=user,
            created_at=response['created_at'],
            raw=response
        )
        return applicant.save()


class Applicant(BaseModel):

    """An Onfido applicant record."""

    GET = 'applicants/{0}'
    POST = 'applicants'

    user = models.ForeignKey(
        User,
        help_text=_("Django user that maps to this applicant.")
    )

    objects = ApplicantQuerySet.as_manager()

    def __unicode__(self):
        return self.user.get_full_name() or self.user.username

    def __repr__(self):
        return u"<Applicant id=%s user='%s'>" % (
            self.id, self.user.username
        )

    def update(self):
        """Fetch latest version from Api and update local data."""
        self.raw = get(format_url(Applicant.GET.format(self.id)))
        return self.save()

    def create_check(
        self, check_type, reports,
        suppress_form_emails=True,
        redirect_uri=None
    ):
        """
        Create a new Check for the current Applicant.

        Args:
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
        return Check.objects.create(self, check_type, reports, suppress_form_emails, redirect_uri)


class CheckQuerySet(models.query.QuerySet):

    """Custom Check queryset."""

    def create(
        self, applicant, check_type, reports,
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
        response = client.Checks.create(applicant.id, data)
        logger.debug(response)
        check = Check(
            id=response['id'],
            created_at=response['created_at'],
            check_type=response['type'],
            result=response['result'],
            user=applicant.user,
            applicant=applicant,
            status=response['status'],
            raw=response
        )
        return check.save()


class Check(BaseModel):

    """The state of an individual check made against an Applicant."""

    CHECK_TYPE_CHOICES = (
        ('express', 'Express check'),
        ('standard', 'Standard check')
    )
    CHECK_STATUS_CHOICES = (
        ('unknown', 'Unknown'),
        ('in_progress', 'In progress'),
        ('awaiting_applicant', 'Awaiting applicant'),
        ('complete', 'Complete'),
        ('withdrawn', 'Withdrawn'),
        ('paused', 'Paused'),
        ('reopened', 'Reopened'),
    )
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
        User,
        help_text=_("The applicant for whom the check is being made."),
        related_name='checks'
    )
    check_type = models.CharField(
        max_length=10,
        choices=CHECK_TYPE_CHOICES,
        help_text=_("See https://documentation.onfido.com/#check-types")
    )
    status = models.CharField(
        max_length=20,
        default='unknown',
        choices=CHECK_STATUS_CHOICES,
        help_text=_("The current state of the check in the checking process.")
    )
    result = models.CharField(
        max_length=20,
        help_text=_("The overall result of the check (derived from reports)."),
        blank=True
    )

    objects = CheckQuerySet.as_manager()

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

    def update(self):
        """Fetch lastest JSON from the API and update raw."""
        response = client.Checks.fetch(self.id)
        self.raw = response
        return self.save()


class Report(BaseModel):

    """Specific reports associated with a Check."""

    REPORT_TYPE_CHOICES = (
        ('identity', 'Identity report'),
        ('document', 'Document report'),
        ('street_level', 'Street level report'),
        ('facial_similarity', 'Facial similarity report'),
    )
    REPORT_STATUS_CHOICES = (
        ('unknown', 'Unknown'),
        ('awaiting_data', 'Awaiting data'),
        ('awaiting_approval', 'Awaiting approval'),
        ('complete', 'Complete'),
        ('withdrawn', 'Withdrawn'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    )
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
        help_text=_("See https://documentation.onfido.com/#reports")
    )
    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS_CHOICES,
        help_text=_("The current state of the report in the checking process."),
        default='unknown'
    )
    result = models.CharField(
        max_length=20,
        help_text=_("The overall result of the report."),
        blank=True
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

    def update(self):
        """Fetch lastest JSON from the API and update raw."""
        response = client.Reports.fetch(self.id)
        self.raw = response
        return self.save()
