from __future__ import annotations

import logging

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..settings import scrub_applicant_data
from .base import BaseModel, BaseQuerySet

logger = logging.getLogger(__name__)


class ApplicantQuerySet(BaseQuerySet):
    """Custom Applicant queryset."""

    def create_applicant(self, user: settings.AUTH_USER_MODEL, raw: dict) -> Applicant:
        """Create a new applicant in Onfido from a user."""
        logger.debug("Creating new Onfido applicant from JSON: %s", raw)
        return Applicant(user=user).parse(raw).save()


class Applicant(BaseModel):
    """An Onfido applicant record."""

    base_href = "applicants"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_("Django user that maps to this applicant."),
        related_name="onfido_applicants",
    )

    objects = ApplicantQuerySet.as_manager()

    def __str__(self) -> str:
        return str(self.user)

    def __repr__(self) -> str:
        return "<Applicant id={} user_id={}>".format(self.id, self.user.id)

    def parse(self, raw_json: dict) -> Applicant:
        """
        Parse the raw value out into other properties.

        Before parsing the data, this method will call the
        scrub_report_data function to remove sensitive data
        so that it is not saved into the local object.

        """
        super().parse(scrub_applicant_data(raw_json))
        return self
