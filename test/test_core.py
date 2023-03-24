import math
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
                zone_maxima = [ v.values(i).max() for i in range(v.num_zones) ]
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
                zone_maxima = [ v.values(i).max() for i in range(v.num_zones) ]
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
                select_vars="z",
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
                select_zones="*:[246]",
            )
            ds = load_and_replace("diff.dat")
            self.assertEqual(ds.num_zones, 3)
            self.assertTrue(ds.zone(0).name.endswith(":2"))
            self.assertTrue(ds.zone(1).name.endswith(":4"))
            self.assertTrue(ds.zone(2).name.endswith(":6"))

class TestExtract(unittest.TestCase):
    ''' Unit tests for extract function '''

    def test_extract(self):
        with test.temp_workspace():
            ds = load_and_replace(test.data_item_path("sphere.dat"))
            self.assertEqual(ds.num_variables,3)
            self.assertEqual(ds.num_zones,6)
            tec_util.extract(
                test.data_item_path("sphere.dat"),
                "extract.dat",
                select_vars=['x','y'],
                select_zones=['*:[246]'],
            )
            ds = load_and_replace("extract.dat")
            self.assertEqual(ds.num_variables,2)
            self.assertEqual(ds.num_zones,3)

class TestMergeDatasets(unittest.TestCase):
    ''' Unit tests for merge_datasets fucntion '''

    def test_merge(self):
        with test.temp_workspace():
            tec_util.merge_datasets(
                test.data_item_path("merge1.dat"),
                test.data_item_path("merge2.dat"),
                "merge.dat",
                warn_duplicates=False
            )
            ds = load_and_replace("merge.dat")
            self.assertEqual(ds.num_variables,5)
            self.assertEqual(ds.num_zones,2)

            # When variable in both dataset, values from dataset2 is used.
            self.assertAlmostEqual(-6.4280895E-05, ds.zone('ZoneA').values('x')[15])

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

class TestRevolveDataset(unittest.TestCase):
    ''' Unit test for the revolve_dataset function '''

    def test_basic_useage(self):
        ''' Test that we can revolve a dataset and get the correct file out '''
        with test.temp_workspace():
            tec_util.revolve_dataset(
                test.data_item_path("axi_sphere.plt"),
                "sphere.plt",
                planes = 13,
                angle  = 90.0,
            )
            ds = load_and_replace("sphere.plt")
            vars = [v.name for v in ds.variables()]
            self.assertEqual(vars,['x','y','z','q1','q2','v1','v2'])
            self.assertEqual(ds.zone(0).dimensions,(11,9,13))
            self.assertEqual(
                ds.zone(0).values('y').minmax(),
                ds.zone(0).values('z').minmax()
            )

    def test_radial_coord(self):
        ''' Verify ability to select the radial coordinate '''
        with test.temp_workspace():
            tec_util.revolve_dataset(
                test.data_item_path("axi_sphere.plt"),
                "sphere.plt",
                radial_coord = 'v2',
                planes = 13,
                angle  = 90.0,
            )
            ds = load_and_replace("sphere.plt")
            vars = [v.name for v in ds.variables()]
            self.assertEqual(vars,['x','y','q1','q2','v1','v2','z'])
            self.assertEqual(
                ds.zone(0).values('v2').minmax(),
                ds.zone(0).values('z').minmax(),
            )

            tec_util.revolve_dataset(
                test.data_item_path("axi_sphere.plt"),
                "sphere.plt",
                radial_coord = {'v2':('ry','rz')},
                planes = 13,
                angle  = 90.0,
            )
            ds = load_and_replace("sphere.plt")
            vars = [v.name for v in ds.variables()]
            self.assertEqual(vars,['x','y','q1','q2','v1','v2','ry','rz'])
            self.assertEqual(
                ds.zone(0).values('v2').minmax(),
                ds.zone(0).values('ry').minmax(),
            )
            self.assertEqual(
                ds.zone(0).values('v2').minmax(),
                ds.zone(0).values('rz').minmax(),
            )

    def test_vector_vars(self):
        ''' Verify we can specify variable to treat as vector quantities '''
        with test.temp_workspace():
            tec_util.revolve_dataset(
                test.data_item_path("axi_sphere.plt"),
                "sphere.plt",
                planes = 13,
                angle  = 90.0,
                vector_vars = ['v1','v2'],
            )
            ds = load_and_replace("sphere.plt")
            vars = [v.name for v in ds.variables()]
            self.assertEqual(vars,['x','y','z','q1','q2','v1','v1_cos','v1_sin','v2','v2_cos','v2_sin'])
            z0 = ds.zone(0)
            self.assertEqual(z0.values('v1').minmax(), z0.values('v1_cos').minmax())
            self.assertEqual(z0.values('v1').minmax(), z0.values('v1_sin').minmax())

            tec_util.revolve_dataset(
                test.data_item_path("axi_sphere.plt"),
                "sphere.plt",
                planes = 13,
                angle  = 90.0,
                vector_vars = {
                    'v1' : ('v1y','v1z'),
                    'v2' : ('v2y','v2z'),
                },
            )
            ds = load_and_replace("sphere.plt")
            vars = [v.name for v in ds.variables()]
            self.assertEqual(vars,['x','y','z','q1','q2','v1','v1y','v1z','v2','v2y','v2z'])
            z0 = ds.zone(0)
            self.assertEqual(z0.values('v1').minmax(), z0.values('v1y').minmax())
            self.assertEqual(z0.values('v1').minmax(), z0.values('v1z').minmax())

    def test_surface_grid(self):
        ''' Verify we can create a surface by revoling a 1D generatrix '''
        with test.temp_workspace():
            tec_util.revolve_dataset(
                test.data_item_path("axi_sphere_surf.plt"),
                "sphere.plt",
                planes = 13,
                angle  = 90.0,
            )
            ds = load_and_replace("sphere.plt")
            vars = [v.name for v in ds.variables()]
            self.assertEqual(vars,['x','y','z','q1','q2','v1','v2'])
            self.assertEqual(ds.zone(0).dimensions,(11,13,1))
            self.assertEqual(
                ds.zone(0).values('y').minmax(),
                ds.zone(0).values('z').minmax()
            )

class TestInterpolate(unittest.TestCase):
    ''' Unit test for the interpolate_datasets function '''

    def test_basic_function(self):
        with test.temp_workspace():
            tec_util.interpolate_dataset(
                test.data_item_path("interp_src.dat"),
                test.data_item_path("interp_tgt.dat"),
                "interp_out.plt",
            )
            ds = load_and_replace("interp_out.plt")
            vrange = ds.variable("r").values(0).minmax()
            self.assertAlmostEqual(max(vrange), 6.39408e-01, delta=1e-6)
            self.assertAlmostEqual(min(vrange), 5.10930e-01, delta=1e-6)
