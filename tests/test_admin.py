from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from onfido.admin import (
    Applicant,
    Check,
    Event,
    EventsMixin,
    RawMixin,
    ResultMixin,
    UserMixin,
)


class ResultMixinTests(TestCase):

    """onfido.admin.ResultMixin tests."""

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


class EventsMixinTests(TestCase):

    """onfido.admin.EventsMixin tests."""

    @mock.patch.object(Check, "events")
    def test__events(self, mock_events):
        now = timezone.now()
        event = Event(
            onfido_id="foo",
            action="test.action",
            resource_type="bar",
            status="in_progress",
            completed_at=now.isoformat(),
            received_at=now.isoformat(),
        ).save()
        mock_events.return_value = [event]
        mixin = EventsMixin()
        check = Check()
        html = mixin._events(check)
        self.assertEqual(
            html, "<ul><li>{}: test.action</li></ul>".format(now.date().isoformat())
        )


class RawMixinTests(TestCase):

    """onfido.admin.RawMixin tests."""

    def test__raw(self):
        mixin = RawMixin()
        obj = Applicant(raw={"foo": "bar"})
        html = mixin._raw(obj)
        self.assertEqual(
            html, '<code>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"foo":&nbsp;"bar"<br>}</code>'
        )

        # test with Decimal (stdlib json won't work) and unicode
        obj = Applicant(raw={"foo": Decimal(1.0), "bar": "åß∂ƒ©˙∆"})
        html = mixin._raw(obj)


class UserMixinTests(TestCase):

    """onfido.admin.UserMixin tests."""

    def test__user(self):
        def assertUser(first_name, last_name, expected):
            mixin = UserMixin()
            user = get_user_model()(first_name=first_name, last_name=last_name)
            obj = mock.Mock(user=user)
            self.assertEqual(mixin._user(obj), expected)

        assertUser("fred", "flintstone", "Fred Flintstone")
        assertUser("", "", "")
        assertUser("fredå", "flintstone", "Fredå Flintstone")
        # this fails, something that title() does to unicode?
        with self.assertRaises(AssertionError):
            self.assertEqual("ƒ", "ƒ".title())
        assertUser("ƒredå", "", "ƒredå".title())
