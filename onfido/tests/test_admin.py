# -*- coding: utf-8 -*-
from decimal import Decimal
import mock

from django.contrib.auth.models import User
from django.test import TestCase

from ..admin import (
    RawMixin,
    UserMixin,
    Applicant
)


class RawMixinTests(TestCase):

    """Tests for RawMixin admin class."""

    def test__raw(self):
        mixin = RawMixin()
        obj = Applicant(raw={'foo': 'bar'})
        html = mixin._raw(obj)
        self.assertEqual(html, '<code>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"foo":&nbsp;"bar"<br>}</code>')

        # test with Decimal (stdlib json won't work) and unicode
        obj = Applicant(raw={'foo': Decimal(1.0), 'bar': u'åß∂ƒ©˙∆'})
        html = mixin._raw(obj)


class UserMixinTests(TestCase):

    """Tests for UserMixin admin class."""

    def test__user(self):

        def assertUser(first_name, last_name, expected):
            mixin = UserMixin()
            user = User(first_name=first_name, last_name=last_name)
            obj = mock.Mock(user=user)
            self.assertEqual(mixin._user(obj), expected)

        assertUser('fred', 'flintstone', 'Fred Flintstone')
        assertUser('', '', '')
        assertUser(u'fredå', 'flintstone', u'Fredå Flintstone')
        # this fails, something that title() does to unicode?
        with self.assertRaises(AssertionError):
            self.assertEqual(u'ƒ', u'ƒ'.title())
        assertUser(u'ƒredå', '', u'ƒredå'.title())
