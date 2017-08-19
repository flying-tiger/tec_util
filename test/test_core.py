import tecplot as tp
import tecplot.constant as tpc
import tec_util
import tempfile
import test
import unittest


class TestDifferenceDatasets(unittest.TestCase):

    load_options = { "read_data_option": tpc.ReadDataOption.Replace }

    def test_nskip(self):

        # default nskip: no variables should be diff'd
        with test.temp_workspace():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff.dat",
            )
            ds = tp.data.load_tecplot("diff.dat", **self.load_options)
            self.assertEqual(
                [ v.name for v in ds.variables() ],
                [ "x", "y", "z" ],
            )
            for v in ds.variables():
                zone_maxima = [ v.values(i).max for i in range(v.num_zones) ]
                self.assertAlmostEqual(max(zone_maxima), 0.5, delta=1e-6)

        # nskip = 1: two variables should be diff'd
        with test.temp_workspace():
            tec_util.difference_datasets(
                test.data_item_path("sphere.dat"),
                test.data_item_path("sphere.dat"),
                "diff.dat",
                nskip=1,
            )
            ds = tp.data.load_tecplot("diff.dat", **self.load_options)
            max_vals = {
                "x" : 1.00,
                "delta_y": 0.00,
                "delta_z": 0.00,
            }
            for v in ds.variables():
                zone_maxima = [ v.values(i).max for i in range(v.num_zones) ]
                self.assertAlmostEqual(max(zone_maxima), max_vals[v.name], delta=1e-6)

    def test_variable_filter(self):

        # Compute delta on just z; keep x as grid variable
        with test.temp_workspace():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff.dat",
                nskip=1,
                var_pattern="z",
            )
            ds = tp.data.load_tecplot("diff.dat", **self.load_options)
            self.assertEqual(ds.num_variables, 2)
            self.assertEqual(ds.variable(0).name, "x")
            self.assertEqual(ds.variable(1).name, "delta_z")

    def test_zone_filter(self):

        # Compute delta on just the even zones
        with test.temp_workspace():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff.dat",
                nskip=1,
                zone_pattern="*:[246]",
            )
            ds = tp.data.load_tecplot("diff.dat", **self.load_options)
            self.assertEqual(ds.num_zones, 3)
            self.assertTrue(ds.zone(0).name.endswith(":2"))
            self.assertTrue(ds.zone(1).name.endswith(":4"))
            self.assertTrue(ds.zone(2).name.endswith(":6"))
