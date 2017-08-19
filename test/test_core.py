import tecplot as tp
import tecplot.constant as tpc
import tec_util
import tempfile
import test
import unittest

class TestDifferenceDatasets(unittest.TestCase):

    def test_nskip(self):

        # default nskip: no variables should be diff'd
        with tempfile.TemporaryDirectory():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff.dat",
            )
            ds = tp.data.load_tecplot("diff.dat")
            self.assertEqual(
                [ v.name for v in ds.variables() ],
                [ "x", "y", "z" ],
            )
            for v in ds.variables():
                zone_maxima = [ v.values(i).max for i in range(v.num_zones) ]
                self.assertAlmostEqual(max(zone_maxima), 0.5, delta=1e-6)

        # nskip = 1: two variables should be diff'd
        with tempfile.TemporaryDirectory():
            tec_util.difference_datasets(
                test.data_item_path("sphere.dat"),
                test.data_item_path("sphere.dat"),
                "diff.dat",
                nskip=1,
            )
            ds = tp.data.load_tecplot("diff.dat", read_data_option=tpc.ReadDataOption.Replace)
            max_vals = {
                "x" : 1.00,
                "delta_y": 0.00,
                "delta_z": 0.00,
            }
            for v in ds.variables():
                zone_maxima = [ v.values(i).max for i in range(v.num_zones) ]
                self.assertAlmostEqual(max(zone_maxima), max_vals[v.name], delta=1e-6)



