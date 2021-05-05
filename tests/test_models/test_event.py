import copy

import pytest
from dateutil.parser import parse as date_parse

from onfido.models import Check, Event, Report

from ..conftest import TEST_EVENT


@pytest.mark.django_db
class TestEventModel:
    def test__resource_manager(self):
        """Test the _resource_manager method."""
        event = Event()
        with pytest.raises(ValueError):
            event._resource_manager()

        event.resource_type = "foo"
        with pytest.raises(ValueError):
            event._resource_manager()

        event.resource_type = "check"
        assert event._resource_manager() == Check.objects
        event.resource_type = "report"
        assert event._resource_manager() == Report.objects

    def test_resource(self, check, event):
        """Test the resource property."""
        # this is really testing the pytest fixture "event", which is built from the
        # TEST_EVENT data - see conftest.py for details.
        assert event.resource == check

    def test_user(self, check, event):
        # this is really testing the pytest fixture "event", which is built from the
        # TEST_EVENT data - see conftest.py for details.
        assert event.user == check.applicant.user

    def test_defaults(self):
        """Test default property values."""
        event = Event()
        # real data taken from check.json
        assert event.resource_type == ""
        assert event.onfido_id == ""
        assert event.action == ""
        assert event.status == ""
        assert event.completed_at is None
        assert event.raw is None

    def test_parse(self):
        """Test the parse_raw method."""
        data = copy.deepcopy(TEST_EVENT)
        event = Event().parse(data)
        # real data taken from check.json
        assert event.resource_type == data["payload"]["resource_type"]
        assert event.onfido_id == data["payload"]["object"]["id"]
        assert event.action == data["payload"]["action"]
        assert event.status == data["payload"]["object"]["status"]
        assert event.completed_at == (
            date_parse(data["payload"]["object"]["completed_at_iso8601"])
        )
