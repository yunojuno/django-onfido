import copy
from unittest import mock

import pytest
from dateutil.parser import parse as date_parse

from onfido.models import Report
from onfido.models.base import BaseModel

from ..conftest import IDENTITY_REPORT_ID, TEST_REPORT_IDENTITY_ENHANCED


@pytest.mark.django_db
class TestReportManager:
    @mock.patch.object(BaseModel, "full_clean")
    def test_create_report(self, mock_clean, user, check):
        """Test the create method parses response."""
        data = copy.deepcopy(TEST_REPORT_IDENTITY_ENHANCED)
        report = Report.objects.create_report(check=check, raw=data)
        assert report.user == user
        assert report.onfido_check == check
        assert report.onfido_id == data["id"]
        assert report.report_type == data["name"]
        assert report.status == data["status"]
        assert report.result == data["result"]
        assert report.created_at == date_parse(data["created_at"])


@pytest.mark.django_db
class TestReportModel:
    def test_defaults(self, check):
        """Test default property values."""
        report = Report(onfido_check=check, onfido_id="foo", report_type="document")
        assert report.onfido_id == "foo"
        assert report.created_at is None
        assert report.status is None
        assert report.result is None
        assert report.report_type == "document"

    def test_parse(self):
        """Test the parse_raw method."""
        data = copy.deepcopy(TEST_REPORT_IDENTITY_ENHANCED)
        assert "breakdown" in data
        assert "properties" in data
        report = Report().parse(data)
        # the default report scrubber should have removed data:
        assert "breakdown" not in report.raw
        assert "properties" not in report.raw
        assert report.onfido_id == IDENTITY_REPORT_ID
        assert report.created_at == date_parse(data["created_at"])
        assert report.status == TEST_REPORT_IDENTITY_ENHANCED["status"]
        assert report.result == TEST_REPORT_IDENTITY_ENHANCED["result"]
        assert report.report_type == TEST_REPORT_IDENTITY_ENHANCED["name"]
