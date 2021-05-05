from __future__ import annotations

import logging

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..settings import scrub_report_data
from .base import BaseQuerySet, BaseStatusModel
from .check import Check

logger = logging.getLogger(__name__)


class ReportQuerySet(BaseQuerySet):
    """Report model queryset."""

    def create_report(self, check: Check, raw: dict) -> Report:
        """Create a new Report from the raw JSON."""
        logger.debug("Creating new Onfido report from JSON: %s", raw)
        return Report(user=check.user, onfido_check=check).parse(raw).save()


class Report(BaseStatusModel):
    """Specific reports associated with a Check."""

    base_href = "reports"

    # v2 API report types - retained for backwards compatibility,
    # but superseded by ReportType
    REPORT_TYPE_CHOICES_DEPRECATED = [
        ("identity", "x Identity report (deprecated)"),
        # ("document", "Document report"),
        ("street_level", "x Street level report (deprecated)"),
        ("facial_similarity", "x Facial similarity report (deprecated)"),
        ("credit", "x Credit report (deprecated)"),
        ("criminal_history", "x Criminal history (deprecated)"),
        # ("right_to_work", "Right to work"),
        ("ssn_trace", "SSN trace (deprecated)"),
    ]

    class ReportType(models.TextChoices):
        # https://documentation.onfido.com/#report-names-in-api
        DOCUMENT = ("document", "Document")
        DOCUMENT_WITH_ADDRESS_INFORMATION = (
            "document_with_address_information",
            "Document with Address Information",
        )
        DOCUMENT_WITH_DRIVING_LICENCE_INFORMATION = (
            "document_with_driving_licence_information",
            "Document with Driving Licence Information",
        )
        FACIAL_SIMILARITY_PHOTO = (
            "facial_similarity_photo",
            "Facial Similarity (photo)",
        )
        FACIAL_SIMILARITY_PHOTO_FULLY_AUTO = (
            "facial_similarity_photo_fully_auto",
            "Facial Similarity (auto)",
        )
        FACIAL_SIMILARITY_VIDEO = (
            "facial_similarity_video",
            "Facial Similarity (video)",
        )
        KNOWN_FACES = ("known_faces", "Known Faces")
        IDENTITY_ENHANCED = ("identity_enhanced", "Identity (enhanced)")
        WATCHLIST_ENHANCED = ("watchlist_enhanced", "Watchlist (enhanced)")
        WATCHLIST_STANDARD = ("watchlist_standard", "Watchlist")
        WATCHLIST_PEPS_ONLY = ("watchlist_peps_only", "Watchlist (PEPs only)")
        WATCHLIST_SANCTIONS_ONLY = (
            "watchlist_sanctions_only",
            "Watchlist (sanctions only)",
        )
        PROOF_OF_ADDRESS = ("proof_of_address", "Proof of Address")
        RIGHT_TO_WORK = ("right_to_work", "Right to Work")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_(
            "The Django user (denormalised from Applicant to make navigation easier)."
        ),  # noqa
        related_name="onfido_reports",
    )
    onfido_check = models.ForeignKey(
        Check,
        on_delete=models.CASCADE,
        help_text=_("Check to which this report is attached."),
        related_name="reports",
    )
    report_type = models.CharField(
        max_length=50,
        choices=ReportType.choices + REPORT_TYPE_CHOICES_DEPRECATED,
        help_text=_(
            "The name of the report - see https://documentation.onfido.com/#reports"
        ),
    )

    objects = ReportQuerySet.as_manager()

    def __str__(self) -> str:
        return "{} for {}".format(
            self.get_report_type_display().capitalize(), self.user
        )

    def __repr__(self) -> str:
        return "<Report id={} type='{}' user_id={}>".format(
            self.id, self.report_type, self.user.id
        )

    def parse(self, raw_json: dict) -> Report:
        """
        Parse the raw value out into other properties.

        Before parsing the data, this method will call the
        scrub_report_data function to remove sensitive data
        so that it is not saved into the local object.

        """
        super().parse(scrub_report_data(raw_json))
        self.report_type = self.raw["name"]
        return self
