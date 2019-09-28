import tecplot as tp
import tecplot.constant as tpc
import tec_util.generators as gen
import shutil
import test
import unittest
import yaml
from os.path import exists

class TestParseSelector(unittest.TestCase):
    ''' Unit tests for parse_selector '''

    def test_basic(self):
        ''' Testing against basic input '''

        # A basic example
        name,index = gen.parse_selector('foo[42]')
        self.assertEqual(name,  'foo')
        self.assertEqual(index, 42)

        # Index should default to zero
        name,index = gen.parse_selector('foo')
        self.assertEqual(name,  'foo')
        self.assertEqual(index, 0)

        # Make sure we're robust to leading/trailing whitespace
        test_strings = [
            'foo',      ' foo',     'foo ',     ' foo ',
            'foo[0]',   ' foo[0]',  'foo[0] ',  ' foo[0] ',
            'foo [0]',  'foo[ 0]',  'foo[0 ]',   'foo[ 0 ]',
            'foo[  0]', 'foo[0  ]',
        ]
        for ts in test_strings:
            name,index = gen.parse_selector(ts)
            self.assertEqual(name, 'foo')
            self.assertEqual(index, 0)

        # Make sure we can handle internal whitespace
        name,index = gen.parse_selector('foo bar [42]')
        self.assertEqual(name,  'foo bar')
        self.assertEqual(index, 42)

class TestDeserializers(unittest.TestCase):
    ''' Unit test for deserialization helper functions '''

    def test_basic_deserializers(self):
        self.assertEqual(gen._PlotType('XYLine'), tpc.PlotType.XYLine)
        self.assertEqual(gen._PlotType('Cartesian2D'), tpc.PlotType.Cartesian2D)
        self.assertEqual(gen._Position([ 1, 2]), (1., 2.))
        self.assertEqual(gen._Position(['1', '2']), (1., 2.))
        self.assertEqual(gen._Position(yaml.safe_load('[1, 2]')), (1., 2.))

class TestLayoutManipulation(unittest.TestCase):
    ''' Unit test for add_page, add_frame, add_xylinemap '''

    def test_basic_generators(self):
        with test.temp_workspace():
            tp.new_layout()
            tp.data.load_tecplot([
                test.data_item_path('spec_data/ds1.dat'),
                test.data_item_path('spec_data/ds2.dat'),
            ])
            default_page = tp.active_page()
            page = gen.add_page()
            default_frame = page.active_frame()
            frame = gen.add_frame(
                position = [ 2., 1.],
                width  = 7,
                height = 5,
            )
            plot = frame.plot(tpc.PlotType.XYLine)
            plot.activate()
            plot.delete_linemaps()
            gen.add_xylinemap(
                name = 'T (ds1)',
                zone = 'stag[0]',
                x_variable = 'x',
                y_variable = 'T',
            )
            gen.add_xylinemap(
                name = 'T (ds2)',
                zone = 'stag[1]',
                x_variable = 'x',
                y_variable = 'T',
            )
            tp.delete_page(default_page)
            page.delete_frame(default_frame)
            tp.save_layout('test.lay')

            # Note: we can't really test for much more than simple success
            # creating the layout file. The fine details of the layout will
            # depend on whether the user has a tecplot.cfg file available
            # and we can't force factory settings in PyTecplot at this time.
            # Therefore, trying to establish a "reference output" is
            self.assertTrue(exists('test.lay'))

    def test_full_example(self):
        with test.temp_workspace():
            shutil.copytree(test.data_item_path('spec_data'),'spec_data')
            with open(test.data_item_path('spec.yml')) as sf:
                spec = yaml.safe_load(sf)
            gen.make_layout(spec['datasets'],spec['pages'],spec['equations'])
            tp.export.save_png('test.png')
            self.assertTrue(exists('test.png'))
