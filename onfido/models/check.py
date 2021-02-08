from __future__ import annotations

import logging

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .applicant import Applicant
from .base import BaseQuerySet, BaseStatusModel

logger = logging.getLogger(__name__)


class CheckQuerySet(BaseQuerySet):
    """Check model manager."""

    def create_check(self, applicant: Applicant, raw: dict) -> Check:
        """Create a new Check object from the raw JSON."""
        logger.debug("Creating new Onfido check from JSON: %s", raw)
        return Check(user=applicant.user, applicant=applicant).parse(raw).save()


class Check(BaseStatusModel):
    """The state of an individual check made against an Applicant."""

    base_href = "checks"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_(
            "The Django user (denormalised from Applicant to make navigation easier)."
        ),  # noqa
        related_name="onfido_checks",
    )
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        help_text=_("The applicant for whom the check is being made."),
        related_name="checks",
    )
    x_check_type = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text=_("DEPRECATED: Check objects no longer support a type."),
    )

    objects = CheckQuerySet.as_manager()

    def __str__(self) -> str:
        return f"Onfido check for {self.user}"

    def __repr__(self) -> str:
        return f"<Check id={self.id} user_id={self.user_id}>"
