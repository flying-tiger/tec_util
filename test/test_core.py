import tecplot as tp
import tecplot.constant as tpc
import tec_util
import tempfile
import test
import unittest

def load_and_replace(dataset_name):
    return tp.data.load_tecplot(dataset_name, read_data_option=tpc.ReadDataOption.Replace)

class TestDifferenceDatasets(unittest.TestCase):
    ''' Unit tests for the difference_datasets function '''

    def test_nskip(self):
        ''' Check behavior of the nskip option '''
        # default nskip: no variables should be diff'd
        with test.temp_workspace():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff.dat",
            )
            ds = load_and_replace("diff.dat")
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
            ds = load_and_replace("diff.dat")
            max_vals = {
                "x" : 1.00,
                "delta_y": 0.00,
                "delta_z": 0.00,
            }
            for v in ds.variables():
                zone_maxima = [ v.values(i).max for i in range(v.num_zones) ]
                self.assertAlmostEqual(max(zone_maxima), max_vals[v.name], delta=1e-6)

    def test_variable_filter(self):
        ''' Test that we can select variables for differencing '''
        # Compute delta on just z; keep x as grid variable
        with test.temp_workspace():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff.dat",
                nskip=1,
                var_pattern="z",
            )
            ds = load_and_replace("diff.dat")
            self.assertEqual(ds.num_variables, 2)
            self.assertEqual(ds.variable(0).name, "x")
            self.assertEqual(ds.variable(1).name, "delta_z")

    def test_zone_filter(self):
        ''' Test that we can select zones for differencing '''
        # Compute delta on just the even zones
        with test.temp_workspace():
            tec_util.difference_datasets(
                test.data_item_path("cube.dat"),
                test.data_item_path("cube.dat"),
                "diff.dat",
                nskip=1,
                zone_pattern="*:[246]",
            )
            ds = load_and_replace("diff.dat")
            self.assertEqual(ds.num_zones, 3)
            self.assertTrue(ds.zone(0).name.endswith(":2"))
            self.assertTrue(ds.zone(1).name.endswith(":4"))
            self.assertTrue(ds.zone(2).name.endswith(":6"))

class TestRenameVariables(unittest.TestCase):
    ''' Unit test for the rename_variables function '''

    def test_basic_rename(self):
        ''' Test that we can rename specific variable in the dataset '''
        with test.temp_workspace():
            tec_util.rename_variables(
                test.data_item_path("cube.dat"),
                "cube.dat",
                { "x":"xx", "z":"zz" }
            )
            ds = load_and_replace("cube.dat")
            self.assertEqual(ds.variable(0).name, "xx")
            self.assertEqual(ds.variable(1).name, "y")
            self.assertEqual(ds.variable(2).name, "zz")

class TestRenameZones(unittest.TestCase):
    ''' Unit test for the rename_zones function '''

    def test_basic_rename(self):
        ''' Test that we can rename specific zones in the dataset '''
        with test.temp_workspace():
            tec_util.rename_zones(
                test.data_item_path("cube.dat"),
                "cube.dat",
                {
                    'cube.x:1' : 'front',
                    'cube.x:6' : 'bottom',
                }
            )
            ds = load_and_replace("cube.dat")
            self.assertEqual(ds.zone(0).name, "front")
            self.assertEqual(ds.zone(5).name, "bottom")

