from unittest import TestCase

import cmdfit.tests.a_test as a_test

# Right now a test to test that I can test. I may change this, but right now it
# just checks the result of 1 + 2.
class TestSum(TestCase):
    def test_calculation(self):
        x=1
        res = a_test.sumtest(x)
        self.assertEqual(res, 3)
