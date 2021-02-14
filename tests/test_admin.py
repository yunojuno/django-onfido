from decimal import Decimal
from unittest import mock

import pytest
from dateutil.parser import parse as date_parse
from django.contrib.auth import get_user_model

from onfido.admin import Applicant, Check, EventsMixin, RawMixin, ResultMixin, UserMixin
from tests.conftest import TEST_EVENT


class TestResultMixin:
    @mock.patch.object(Check, "mark_as_clear")
    def test__events(self, mock_clear):
        def request():
            request = mock.Mock()
            request.user = get_user_model()()
            return request

        check = Check()
        request = request()
        mixin = ResultMixin()
        mixin.mark_as_clear(request, [check])
        mock_clear.assert_called_once_with(request.user)


@pytest.mark.django_db
class TestEventsMixin:

    """onfido.admin.EventsMixin tests."""

    @mock.patch.object(Check, "events")
    def test__events(self, mock_events, event):
        payload = TEST_EVENT["payload"]
        action = payload["action"]
        completed_at = date_parse(payload["object"]["completed_at_iso8601"])
        mock_events.return_value = [event]
        mixin = EventsMixin()
        check = Check()
        html = mixin._events(check)
        assert html == (f"<ul><li>{completed_at.date()}: {action}</li></ul>")


class TestRawMixin:
    def test__raw(self):
        mixin = RawMixin()
        obj = Applicant(raw={"foo": "bar"})
        html = mixin._raw(obj)
        assert (
            html == '<code>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"foo":&nbsp;"bar"<br>}</code>'
        )

        # test with Decimal (stdlib json won't work) and unicode
        obj = Applicant(raw={"foo": Decimal(1.0), "bar": "åß∂ƒ©˙∆"})
        html = mixin._raw(obj)


class TestUserMixin:
    def test__user(self):
        def assertUser(first_name, last_name, expected):
            mixin = UserMixin()
            user = get_user_model()(first_name=first_name, last_name=last_name)
            obj = mock.Mock(user=user)
            assert mixin._user(obj) == expected

        assertUser("fred", "flintstone", "Fred Flintstone")
        assertUser("", "", "")
        assertUser("fredå", "flintstone", "Fredå Flintstone")
