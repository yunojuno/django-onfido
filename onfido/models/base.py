from __future__ import annotations

import datetime
import logging
from typing import Any

from dateutil.parser import parse as date_parse
from django.conf import settings
from django.db import models
from django.utils.timezone import now as tz_now
from django.utils.translation import gettext_lazy as _

from ..api import get
from ..signals import on_completion, on_status_change
from .event import Event

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    """Base model used to set timestamps."""

    # used to format the href - override in subclasses
    base_href = ""

    onfido_id = models.CharField(
        "Onfido ID",
        unique=True,
        max_length=40,
        help_text=_("The id returned from the Onfido API."),
    )
    created_at = models.DateTimeField(
        help_text=_("The timestamp returned from the Onfido API."),
        blank=True,
        null=True,
    )
    raw = models.JSONField(
        help_text=_("The raw JSON returned from the API."), blank=True, null=True
    )

    class Meta:
        abstract = True

    @property
    def href(self) -> str:
        """Return the href from base_href."""
        return f"{self.base_href}/{self.onfido_id}"

    def save(self, *args: Any, **kwargs: Any) -> BaseModel:
        """Save object and return self (for chaining methods)."""
        self.full_clean()
        super().save(*args, **kwargs)
        return self

    def parse(self, raw_json: dict) -> BaseModel:
        """Parse the raw value out into other properties."""
        self.raw = raw_json
        self.onfido_id = self.raw["id"]
        self.created_at = date_parse(self.raw["created_at"])
        return self

    def fetch(self) -> BaseModel:
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

    def pull(self) -> BaseModel:
        """
        Update the object from the remote API.

        Named after the git operation - this will call fetch(), and
        then save the object.

        Returns the updated object (saved).

        """
        return self.fetch().save()


class BaseQuerySet(models.QuerySet):
    """Custom queryset for models subclassing BaseModel."""

    def fetch(self) -> None:
        """Call fetch method on all objects in the queryset."""
        for obj in self:
            try:
                obj.fetch()
            except Exception:  # noqa: B902
                logger.exception("Failed to fetch Onfido object: %r", obj)

    def pull(self) -> None:
        """Call pull method on all objects in the queryset."""
        for obj in self:
            try:
                obj.pull()
            except Exception:  # noqa: B902
                logger.exception("Failed to pull Onfido object: %r", obj)


class BaseStatusModel(BaseModel):
    """Base class for models with a status and result field."""

    class Status(models.TextChoices):
        """Combined list of status values for check / report."""

        AWAITING_APPLICANT = ("awaiting_applicant", "Awaiting applicant")
        AWAITING_APPROVAL = ("awaiting_approval", "Awaiting approval")
        AWAITING_DATA = ("awaiting_data", "Awaiting data")
        CANCELLED = ("cancelled", "Cancelled")
        COMPLETE = ("complete", "Complete")
        IN_PROGRESS = ("in_progress", "In progress")
        PAUSED = ("paused", "Paused")
        REOPENED = ("reopened", "Reopened")
        WITHDRAWN = ("withdrawn", "Withdrawn")

    class Result(models.TextChoices):
        """Combined list of result values for check / report."""

        CLEAR = ("clear", "Clear")
        CONSIDER = ("consider", "Consider")
        UNIDENTIFIED = ("unidentified", "Unidentified")

    status = models.CharField(
        max_length=20,
        help_text=_("The current state of the check / report (from API)."),
        choices=Status.choices,
        db_index=True,
        blank=True,
        null=True,
    )
    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        help_text=_("The final result of the check / reports (from API)."),
        blank=True,
        null=True,
    )
    updated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("The timestamp of the most recent status change (from API)."),
    )

    class Meta:
        abstract = True

    def events(self) -> BaseQuerySet:
        """Return queryset of Events related to this object."""
        # prevents circ. import
        from .event import Event

        return Event.objects.filter(
            onfido_id=self.onfido_id, resource_type=self._meta.model_name
        )

    def _override_event(self, user: settings.AUTH_USER_MODEL) -> Event:
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
                    "completed_at_iso8601": tz_now().isoformat(),
                    "href": self.href,
                    "id": self.onfido_id,
                    "status": self.status,
                },
                "resource_type": self._meta.model_name,
                "user_id": user.id,
            }
        }
        return Event().parse(payload)

    def update_status(self, event: Event) -> Event:
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
        if not isinstance(event.completed_at, datetime.datetime):
            raise ValueError("event.completed_at is not a datetime object")
        # swap statuses around so we record old / new
        self.status, old_status = event.status, self.status
        self.updated_at = event.completed_at
        try:
            self.pull()
        except Exception:  # noqa: B902
            # even if we can't get latest, we should save the changes we
            # have already made to the object
            logger.warning("Unable to pull latest from Onfido: '%r'", self)
            self.save()
        on_status_change.send(
            self.__class__,
            instance=self,
            event=event.action,
            status_before=old_status,
            status_after=event.status,
        )
        if event.status == self.Status.COMPLETE:
            on_completion.send(self.__class__, instance=self)
        return self

    def parse(self, raw_json: dict) -> Event:
        """Parse the raw value out into other properties."""
        super().parse(raw_json)
        self.result = self.raw["result"]
        self.status = self.raw["status"]
        return self

    def mark_as_clear(self, user: settings.AUTH_USER_MODEL) -> Event:
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
        event = self._override_event(user)
        event.raw["payload"]["result"] = self.Result.CLEAR
        event.save()

        self.result = self.Result.CLEAR
        self.save()
        return self

    @property
    def is_clear(self) -> bool:
        """Return True/False to whether a check is successful and clear."""
        return self.result == self.Result.CLEAR
