import copy

import pytest
from dateutil.parser import parse as date_parse
from django.contrib.auth import get_user_model

from onfido.models import Applicant
from onfido.settings import scrub_applicant_data

from ..conftest import APPLICANT_ID, TEST_APPLICANT

User = get_user_model()


@pytest.mark.django_db
class TestApplicantManager:
    def test_create_applicant(self, user):
        """Test the create method parses response."""
        data = copy.deepcopy(TEST_APPLICANT)
        applicant = Applicant.objects.create_applicant(user=user, raw=data)
        assert applicant.user == user
        assert applicant.raw == scrub_applicant_data(data)
        assert applicant.onfido_id == data["id"]
        assert applicant.created_at == date_parse(data["created_at"])


@pytest.mark.django_db
class TestApplicantModel:
    def test_defaults(self, user):
        """Test default property values."""
        applicant = Applicant(user=user, onfido_id=APPLICANT_ID, raw=TEST_APPLICANT)
        assert applicant.href == f"applicants/{APPLICANT_ID}"
        assert applicant.onfido_id == APPLICANT_ID
        assert applicant.user == user
        assert applicant.created_at is None

    def test_save(self, user):
        """Test the save method."""
        applicant = Applicant(user=user, onfido_id=APPLICANT_ID, raw=TEST_APPLICANT)
        applicant.save()
        assert applicant.href == f"applicants/{APPLICANT_ID}"
        assert applicant.onfido_id == APPLICANT_ID
        assert applicant.user == user
        assert applicant.created_at is None
        # test the related_name
        assert user.onfido_applicants.last() == applicant

    def test_parse(self, applicant):
        """Test default scrubbing of data."""
        data = copy.deepcopy(TEST_APPLICANT)
        assert "address" in TEST_APPLICANT
        assert "dob" in TEST_APPLICANT
        applicant.parse(data)
        assert applicant.raw == {
            "id": TEST_APPLICANT["id"],
            "created_at": TEST_APPLICANT["created_at"],
            "href": TEST_APPLICANT["href"],
        }
