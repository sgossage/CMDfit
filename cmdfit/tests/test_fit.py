from unittest import TestCase
import os
import cmdfit.tests.a_test as a_test
import cmdfit.processing.columnread as cread

# Right now a test to test that I can test. I may change this, but right now it
# just checks the result of 1 + 2.
class TestSum(TestCase):
    def test_calculation(self):
        x=1
        res = a_test.sumtest(x)
        self.assertEqual(res, 3)

class TestIO(TestCase):
    def test_io(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = root_dir + '/data'
        specific_data_dir = data_dir + '/Hyades'
        data_file = specific_data_dir + '/vanleeuwen_out.txt'
        
        test_data = cread.get_header(data_file)
        
        self.assertEqual(test_data[3], 'DEC')
