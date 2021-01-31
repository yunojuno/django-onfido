"""Full integration test - do not run in CI."""
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from onfido.helpers import create_applicant, create_check
from onfido.models import Report

User = get_user_model()


@pytest.mark.skipif(
    bool(not settings.TEST_INTEGRATION), reason="TEST_INTEGRATION is False"
)
@pytest.mark.django_db
def test_end_to_end():
    user = User.objects.create(
        username="fred",
        first_name="Fred",
        last_name="Consider",
        email="fred@example.com",
    )
    applicant = create_applicant(user)
    check = create_check(applicant, report_names=[Report.ReportType.IDENTITY_ENHANCED])
    assert not check.is_clear
