from __future__ import annotations

import logging

from dateutil.parser import parse as date_parse
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..compat import JSONField

logger = logging.getLogger(__name__)


class Event(models.Model):
    """Used to record callback events received from the API."""

    onfido_id = models.CharField(
        "Onfido ID",
        max_length=40,
        help_text=_("The Onfido ID of the related resource."),
    )
    resource_type = models.CharField(
        max_length=20, help_text=_("The resource_type returned from the API callback.")
    )
    action = models.CharField(
        max_length=20, help_text=_("The event name as returned from the API callback.")
    )
    status = models.CharField(
        max_length=20, help_text=_("The status of the object after the event.")
    )
    completed_at = models.DateTimeField(
        help_text=_("The timestamp returned from the Onfido API."),
        blank=True,
        null=True,
    )
    received_at = models.DateTimeField(
        help_text=_("The timestamp when the server received the event."),
    )
    raw = JSONField(
        help_text=_("The raw JSON returned from the API."), blank=True, null=True
    )

    class Meta:
        ordering = ["completed_at"]

    def __str__(self) -> str:
        return "{} event occurred on {}.{}".format(
            self.action, self.resource_type, self.onfido_id
        )

    def __repr__(self) -> str:
        return "<Event id={} action='{}' onfido_id='{}.{}'>".format(
            self.id, self.action, self.resource_type, self.onfido_id
        )

    def _resource_manager(self) -> models.Manager:
        """Return the appropriate model manager for the resource_type."""
        if self.resource_type not in (
            "check",
            "report",
        ):
            raise ValueError(f"Unknown resource type: {self.resource_type}")
        if self.resource_type == "check":
            from .check import Check

            return Check.objects
        elif self.resource_type == "report":
            from .report import Report

            return Report.objects

    @property
    def resource(self) -> models.Manager:
        """Return the underlying Check or Report resource."""
        return self._resource_manager().get(onfido_id=self.onfido_id)

    @property
    def user(self) -> settings.AUTH_USER_MODEL:
        """Return the user to whom the resource refers."""
        return self.resource.user

    def parse(self, raw_json: dict) -> Event:
        """Parse the raw value out into other properties."""
        self.raw = raw_json
        payload = self.raw["payload"]
        self.resource_type = payload["resource_type"]
        self.action = payload["action"]
        obj = payload["object"]
        self.onfido_id = obj["id"]
        self.status = obj["status"]
        self.completed_at = date_parse(obj["completed_at_iso8601"])
        return self
