import tecplot as tp
import tec_util
import tempfile
import test
import unittest

class TestDifferenceDatasets(unittest.TestCase):

    def test_nskip(self):
        with tempfile.TemporaryDirectory():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff1.dat",
                nskip=1,
            )
