import tecplot as tp
import tecplot.constant as tpc
import test
import unittest
from tec_util.__main__ import main

def load_and_replace(dataset_name):
    return tp.data.load_tecplot(dataset_name, read_data_option=tpc.ReadDataOption.Replace)

class TestMain(unittest.TestCase):
    ''' Tests for the main program '''

    def test_interp(self):
        ''' Make sure interp command works '''
        with test.temp_workspace():
            main([
                'interp',
                test.data_item_path('interp_src.dat'),
                test.data_item_path('interp_tgt.dat'),
            ])
            ds = load_and_replace("interp.plt")
            vrange = ds.variable("r").values(0).minmax
            self.assertAlmostEqual(max(vrange), 6.39408e-01, delta=1e-6)
            self.assertAlmostEqual(min(vrange), 5.10930e-01, delta=1e-6)
