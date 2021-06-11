import copy

import pytest
from dateutil.parser import parse as date_parse

from onfido.models import Check

from ..conftest import APPLICANT_ID, TEST_CHECK


@pytest.mark.django_db
class TestCheckManager:
    """onfido.models.ApplicantManager tests."""

    def test_create_check(self, user, applicant):
        """Test the create method parses response."""
        data = copy.deepcopy(TEST_CHECK)
        check = Check.objects.create_check(applicant=applicant, raw=data)
        assert check.user == user
        assert check.applicant == applicant
        assert check.onfido_id == data["id"]
        assert check.status == data["status"]
        assert check.result == data["result"]
        assert check.created_at == date_parse(data["created_at"])


@pytest.mark.django_db
class TestCheckModel:
    """onfido.models.Check tests."""

    def test_defaults(self, user, applicant):
        """Test default property values."""
        check = Check(
            user=user, applicant=applicant, onfido_id=APPLICANT_ID, raw=TEST_CHECK
        )
        assert check.onfido_id == APPLICANT_ID
        assert check.raw == TEST_CHECK
        assert check.created_at is None
        assert check.status is None
        assert check.result is None

    def test_parse(self):
        """Test the parse_raw method."""
        data = copy.deepcopy(TEST_CHECK)
        check = Check().parse(data)
        assert check.onfido_id == TEST_CHECK["id"]
        assert check.created_at == date_parse(TEST_CHECK["created_at"])
        assert check.status == "in_progress"
        assert check.result is None
