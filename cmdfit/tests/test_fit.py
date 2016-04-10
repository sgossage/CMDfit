from unittest import TestCase

import cmdfit

# Right now a test to test that I can test...cmdfit will change and
# the test will be more meaningful in the future (i.e. it will not return
# just x + 2).
class TestFit(TestCase):
    def test_is_string(self):
        a = cmdfit.fit(1)
        self.assertEqual(a, 3)
