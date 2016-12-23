# -*- coding: utf-8 -*-
import datetime
import logging

from dateutil.parser import parse as date_parse

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now as tz_now

from .api import get
from .settings import scrub_report_data
from .signals import on_status_change, on_completion

logger = logging.getLogger(__name__)


class BaseModel(models.Model):

    """Base model used to set timestamps."""

    onfido_id = models.CharField(
        'Onfido ID',
        unique=True,
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

    @property
    def href(self):
        """Return the href from the raw JSON field."""
        return self.raw['href']

    def save(self, *args, **kwargs):
        """Save object and return self (for chaining methods)."""
        self.full_clean()
        super(BaseModel, self).save(*args, **kwargs)
        return self

    def parse(self, raw_json):
        """Parse the raw value out into other properties."""
        self.raw = raw_json
        self.onfido_id = self.raw['id']
        self.created_at = date_parse(self.raw['created_at'])
        return self

    def fetch(self):
        """
        Fetch the object JSON from the remote API.

        Named after the git operation - this will call the API for the
        latest JSON representation, and update the local fields, but will
        not save the updates. This is useful for inspecting the API response
        without making permanent changes to the object. It can also be used
        to interact with the API without saving an objects:

        >>> obj = Check(onfido_id='123').fetch()

        Returns the updated object (unsaved).

        """
        return self.parse(get(self.href))

    def pull(self):
        """
        Update the object from the remote API.

        Named after the git operation - this will call fetch(), and
        then save the object.

        Returns the updated object (saved).

        """
        return self.fetch().save()


class BaseQuerySet(models.QuerySet):

    """Custom queryset for models subclassing BaseModel."""

    def fetch(self):
        """Call fetch method on all objects in the queryset."""
        for obj in self:
            try:
                obj.fetch()
            except:
                logger.exception("Failed to fetch Onfido object: %r", obj)

    def pull(self):
        """Call pull method on all objects in the queryset."""
        for obj in self:
            obj.pull()


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
        db_index=True,
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
    is_clear = models.NullBooleanField(
        default=None,
        help_text=_("True if the check / report is 'clear' (via API or manual override).")
    )

    class Meta:
        abstract = True

    def events(self):
        """Return queryset of Events related to this object."""
        return Event.objects.filter(onfido_id=self.onfido_id, resource_type=self._meta.model_name)

    def _override_event(self, user):
        """
        Create a fake override event for the object.

        This method uses the current object to create a fake Event payload,
        which is then parsed into an Event object, used to fake result
        transitions.

        NB the Event object isn't saved in this method.

        Args:
            user: User object, the person who is making the fake transition (
                used for auditing purposes).

        Returns a new (unsaved) Event that can be used to audit a fake transition.

        """
        payload = {
            "payload": {
                "action": "manual.override",
                "object": {
                    "completed_at": tz_now().isoformat(),
                    "href": self.href,
                    "id": self.onfido_id,
                    "status": self.status
                },
                "resource_type": self._meta.model_name,
                "user_id": user.id
            }

        }
        return Event().parse(payload)

    def update_status(self, event):
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
            event: Event object containing the update information

        Returns the updated object.

        """
        # we're doing a lot of marshalling from JSON to python, so this assert
        # just ensures we do actually have a datetime at this point
        assert isinstance(event.completed_at, datetime.datetime)
        # swap statuses around so we record old / new
        self.status, old_status = event.status, self.status
        self.updated_at = event.completed_at
        try:
            self.pull()
        except:
            # even if we can't get latest, we should save the changes we
            # have already made to the object
            logger.warn(u"Unable to pull latest from Onfido: '%r'", self)
            self.save()
        on_status_change.send(
            self.__class__,
            instance=self,
            event=event.action,
            status_before=old_status,
            status_after=event.status
        )
        if event.status == 'complete':
            on_completion.send(self.__class__, instance=self)
        return self

    def parse(self, raw_json):
        """Parse the raw value out into other properties."""
        super(BaseStatusModel, self).parse(raw_json)
        self.result = self.raw['result']
        self.status = self.raw['status']
        if self.result == 'clear':
            self.is_clear = True
        return self

    def mark_as_clear(self, user):
        """
        Override the result field manually.

        When a Check / Report comes back as 'consider', and we need to get to
        some kind of answer ourselves (outside of Onfido). If we decided (offline)
        that the applicant is OK (e.g. their passport photo may be poor quality,
        so Onfido return 'consider', but we then take a view that it's correct)
        we need to mark them as cleared, so that they have the approval state.

        The important thing here is that we correctly audit the change - we don't
        just overwrite the result field, but we log the change, so that it can
        be seen. In order to do this we piggy-back on the event update process,
        and use a fake event (one that we create, not Onfido) to update the
        result.

        Args:
            user: User object, the person who is doing the overriding - this
                will typically be an admin user, doing it from the admin site.

        Returns the object itself, updated and saved.

        """
        self._override_event(user).save()
        self.is_clear = True
        self.save()
        return self


class ApplicantQuerySet(BaseQuerySet):

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

    objects = ApplicantQuerySet.as_manager()

    def __unicode__(self):
        return u"{}".format(self.user.get_full_name() or self.user.username)

    def __repr__(self):
        return u"<Applicant id={} user_id={}>".format(
            self.id, self.user.id
        )


class CheckQuerySet(BaseQuerySet):

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

    objects = CheckQuerySet.as_manager()

    def __unicode__(self):
        return u"{} for {}".format(
            self.get_check_type_display().capitalize(),
            self.user.get_full_name() or self.user.username
        )

    def __repr__(self):
        return u"<Check id={} type='{}' user_id={}>".format(
            self.id,
            self.check_type,
            self.user.id
        )

    def parse(self, raw_json):
        """Parse the raw value out into other properties."""
        super(Check, self).parse(raw_json)
        self.check_type = self.raw['type']
        return self


class ReportQuerySet(BaseQuerySet):

    """Report model queryset."""

    def create_report(self, check, raw):
        """Create a new Report from the raw JSON."""
        logger.debug("Creating new Onfido report from JSON: %s", raw)
        return (
            Report(user=check.user, onfido_check=check)
            .parse(raw)
            .save()
        )


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

    objects = ReportQuerySet.as_manager()

    def __unicode__(self):
        return u"{} for {}".format(
            self.get_report_type_display().capitalize(),
            self.user.get_full_name() or self.user.username
        )

    def __repr__(self):
        return u"<Report id={} type='{}' user_id={}>".format(
            self.id,
            self.report_type,
            self.user.id
        )

    def parse(self, raw_json):
        """
        Parse the raw value out into other properties.

        Before parsing the data, this method will call the
        scrub_report_data function to remove sensitive data
        so that it is not saved into the local object.

        """
        scrub_report_data(raw_json)
        super(Report, self).parse(raw_json)
        self.report_type = self.raw['name']
        return self


class Event(models.Model):

    """Used to record callback events received from the API."""

    onfido_id = models.CharField(
        'Onfido ID',
        max_length=40,
        help_text=_("The Onfido ID of the related resource."),
    )
    resource_type = models.CharField(
        max_length=20,
        help_text=_("The resource_type returned from the API callback.")
    )
    action = models.CharField(
        max_length=20,
        help_text=_("The event name as returned from the API callback.")
    )
    status = models.CharField(
        max_length=20,
        help_text=_("The status of the object after the event.")
    )
    completed_at = models.DateTimeField(
        help_text=_("The timestamp returned from the Onfido API."),
        blank=True, null=True
    )
    raw = JSONField(
        help_text=_("The raw JSON returned from the API."),
        blank=True, null=True
    )

    class Meta:
        ordering = ['completed_at']

    def __unicode__(self):
        return "{} event occurred on {}.{}".format(
            self.action, self.resource_type, self.onfido_id
        )

    def __repr__(self):
        return u"<Event id={} action='{}' onfido_id='{}.{}'>".format(
            self.id, self.action, self.resource_type, self.onfido_id
        )

    def _resource_manager(self):
        """Return the appropriate model manager for the resource_type."""
        assert self.resource_type in ('check', 'report'), (
            "Unknown resource type: {}".format(self.resource_type)
        )
        if self.resource_type == 'check':
            return Check.objects
        elif self.resource_type == 'report':
            return Report.objects

    @property
    def resource(self):
        """Return the underlying Check or Report resource."""
        return self._resource_manager().get(onfido_id=self.onfido_id)

    @property
    def user(self):
        """Return the user to whom the resource refers."""
        return self.resource.user

    def save(self, *args, **kwargs):
        """Save object and return self (for chaining methods)."""
        self.full_clean()
        super(Event, self).save(*args, **kwargs)
        return self

    def parse(self, raw_json):
        """Parse the raw value out into other properties."""
        self.raw = raw_json
        payload = self.raw['payload']
        self.resource_type = payload['resource_type']
        self.action = payload['action']
        obj = payload['object']
        self.onfido_id = obj['id']
        self.status = obj['status']
        self.completed_at = date_parse(obj['completed_at'])
        return self
