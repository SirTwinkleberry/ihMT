from ihmt.meta import _Event, Signal

from unittest import TestCase, skip

from numpy import set_printoptions
from sys import maxsize

set_printoptions(precision=maxsize)


@skip
class TestSignal(TestCase):
    def test_CM_in_ALT(self):
        self.assertFalse(Signal.CM in Signal.ALT)

    def test_ALT_in_CM(self):
        self.assertFalse(Signal.ALT in Signal.CM)

    def test_BP_in_ALT(self):
        self.assertFalse(Signal.BP in Signal.ALT)

    def test_BP_in_CM(self):
        self.assertFalse(Signal.BP in Signal.CM)

    def test_ALT_in_BP(self):
        self.assertTrue(Signal.ALT in Signal.BP)

    def test_CM_in_BP(self):
        self.assertTrue(Signal.CM in Signal.BP)


class TestMeta(TestCase): ...
