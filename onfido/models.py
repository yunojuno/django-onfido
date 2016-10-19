# -*- coding: utf-8 -*-
import datetime
import logging

from dateutil.parser import parse as date_parse

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

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
        help_text=_("The timestamp returned from the Onfido API."),
        blank=True, null=True
    )
    raw = JSONField(
        help_text=_("The raw JSON returned from the API."),
        blank=True, null=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Save object and return self (for chaining methods)."""
        self.full_clean()
        super(BaseModel, self).save(*args, **kwargs)
        return self

    def parse(self, raw_json):
        """Parses the raw value out into other properties."""
        self.raw = raw_json
        self.id = self.raw['id']
        self.created_at = date_parse(self.raw['created_at'])
        return self


class BaseStatusModel(BaseModel):

    """Base class for models with a status and result field."""

    CHECK_STATUS_CHOICES = (
        ('in_progress', 'In progress'),
        ('awaiting_applicant', 'Awaiting applicant'),
        ('complete', 'Complete'),
        ('withdrawn', 'Withdrawn'),
        ('paused', 'Paused'),
        ('reopened', 'Reopened'),
    )
    REPORT_STATUS_CHOICES = (
        ('awaiting_data', 'Awaiting data'),
        ('awaiting_approval', 'Awaiting approval'),
        ('complete', 'Complete'),
        ('withdrawn', 'Withdrawn'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    )
    STATUS_CHOICES = (
        ('Check', CHECK_STATUS_CHOICES),
        ('Report', REPORT_STATUS_CHOICES)
    )
    CHECK_RESULT_CHOICES = (
        ('clear', 'Clear'),
        ('consider', 'Consider')
    )
    REPORT_RESULT_CHOICES = (
        ('clear', 'Clear'),
        ('consider', 'Consider'),
        ('unidentified', 'Unidentified'),
    )
    RESULT_CHOICES = (
        ('Check', CHECK_RESULT_CHOICES),
        ('Report', REPORT_RESULT_CHOICES),
    )

    status = models.CharField(
        max_length=20,
        help_text=_("The current state of the check / report (from API)."),
        choices=STATUS_CHOICES,
        blank=True, null=True
    )
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        help_text=_("The final result of the check / reports (from API)."),
        blank=True, null=True
    )
    updated_at = models.DateTimeField(
        blank=True, null=True,
        help_text=_("The timestamp of the most recent status change (from API).")
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
        # we're doing a lot of marshalling from JSON to python, so this assert
        # just ensures we do actually have a datetime at this point
        assert isinstance(timestamp, datetime.datetime)
        # swap statuses around so we record old / new
        self.status, old_status = new_status, self.status
        self.updated_at = timestamp
        self.save()
        on_status_change.send(
            self.__class__,
            instance=self,
            event=event,
            status_before=old_status,
            status_after=new_status
        )
        if new_status == 'complete':
            on_completion.send(self.__class__, instance=self)
        return self

    def parse(self, raw_json):
        """Parses the raw value out into other properties."""
        super(BaseStatusModel, self).parse(raw_json)
        self.result = self.raw['result']
        self.status = self.raw['status']
        return self


class ApplicantManager(models.Manager):

    """Custom Applicant queryset."""

    def create_applicant(self, user, raw):
        """Create a new applicant in Onfido from a user."""
        logger.debug("Creating new Onfido applicant from JSON: %s", raw)
        return Applicant(user=user).parse(raw).save()


class Applicant(BaseModel):

    """An Onfido applicant record."""

    user = models.OneToOneField(
        User,
        help_text=_("Django user that maps to this applicant."),
        related_name='onfido_applicant'
    )

    objects = ApplicantManager()

    def __unicode__(self):
        return self.user.get_full_name() or self.user.username

    def __repr__(self):
        return u"<Applicant id=%s user='%s'>" % (
            self.id, self.user.username
        )


class CheckManager(models.Manager):

    """Check model manager."""

    def create_check(self, applicant, raw):
        """Create a new Check object from the raw JSON."""
        logger.debug("Creating new Onfido check from JSON: %s", raw)
        return Check(user=applicant.user, applicant=applicant).parse(raw).save()


class Check(BaseStatusModel):

    """The state of an individual check made against an Applicant."""

    CHECK_TYPE_CHOICES = (
        ('express', 'Express check'),
        ('standard', 'Standard check')
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

    objects = CheckManager()

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

    def parse(self, raw_json):
        """Parses the raw value out into other properties."""
        super(Check, self).parse(raw_json)
        self.check_type = self.raw['type']
        return self


class ReportManager(models.Manager):

    """Report model manager."""

    def create_report(self, check, raw):
        """Create a new Report from the raw JSON."""
        logger.debug("Creating new Onfido report from JSON: %s", raw)
        return Report(user=check.user, onfido_check=check).parse(raw).save()


class Report(BaseStatusModel):

    """Specific reports associated with a Check."""

    REPORT_TYPE_CHOICES = (
        ('identity', 'Identity report'),
        ('document', 'Document report'),
        ('street_level', 'Street level report'),
        ('facial_similarity', 'Facial similarity report'),
        ('credit', 'Credit report'),
        ('criminal_history', 'Criminal history'),
        ('right_to_work', 'Right to work'),
        ('ssn_trace', 'SSN trace'),
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

    objects = ReportManager()

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

    def parse(self, raw_json):
        """Parses the raw value out into other properties."""
        super(Report, self).parse(raw_json)
        self.report_type = self.raw['name']
        return self
