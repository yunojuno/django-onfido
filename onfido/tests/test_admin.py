# -*- coding: utf-8 -*-
from decimal import Decimal

from django.test import TestCase

from ..admin import (
    RawMixin,
    Applicant
)


class RawMixinTests(TestCase):

    def test__raw(self):
        mixin = RawMixin()
        obj = Applicant(raw={'foo': 'bar'})
        html = mixin._raw(obj)
        self.assertEqual(html, '<code>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"foo":&nbsp;"bar"<br>}</code>')

        # test with Decimal (stdlib json won't work) and unicode
        obj = Applicant(raw={'foo': Decimal(1.0), 'bar': u'åß∂ƒ©˙∆'})
        html = mixin._raw(obj)
