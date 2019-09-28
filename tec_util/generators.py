import logging
import re
import tecplot as tp
import tecplot.constant as tpc

log = logging.getLogger(__name__)


#-----------------------------------------------------------------------
# Helper Functions
#-----------------------------------------------------------------------
def parse_selector(selector):
    ''' Get base/index from a selector expression.

        A selector consistis of a base string and an options interger
        index enclosed in square brackets, e.g. "foo[123]". If the index
        is omitted, a default of 0 is returned. Leading/trailing whitespace
        for the base string is removed (but not internal whitespace)
    '''
    selector_pattern = re.compile('^([^\[]+)(\[\s*(\d+)\s*\])?$')
    match = re.fullmatch(selector_pattern, selector.strip())
    if not match:
        raise RuntimeError(f'Invalid zone/variable selector "{selector}"')
    base, _, index = match.groups(default=0)
    return base.strip(), int(index)

def set_attributes(obj, attr_dict, attr_types, verbose=False):
    ''' Set object attributes from dictionary w/ type conversion '''
    for k,v in attr_dict.items():
        vtype = attr_types.get(k)
        if not vtype:
            log.warning('Ignoring unsupported %s attribute "%s"',
                        type(obj).__name__, k)
            continue
        if verbose:
            print(f'{k}: {v}')
        setattr(obj,k,vtype(v))


#-----------------------------------------------------------------------
# De-serializers: Convert dicts/strings to Tecplot enums/objects
#-----------------------------------------------------------------------
def _Color(name):
    return tpc.Color[name]

def _FillMode(name):
    return tpc.FillMode[name]

def _Pattern(name):
    return tpc.LinePattern[name]

def _PlotType(name):
    return tpc.PlotType[name]

def _Position(pair):
    return (float(pair[0]), float(pair[1]))

def _StepMode(name):
    return tpc.StepMode[name]

def _SymbolShape(name):
    return tpc.GeomShape[name]

def _SymbolType(name):
    return tpc.SymbolType[name]

def _Variable(selector, dataset=None):
    name, index = parse_selector(selector)
    if not dataset:
        dataset = tp.active_frame().dataset
    variables = list(dataset.variables(name))
    if not variables:
        raise RuntimeError(f'No variables matching "{name}"')
    return variables[index]

def _Zone(selector, dataset=None):
    name, index = parse_selector(selector)
    if not dataset:
        dataset = tp.active_frame().dataset
    zones = list(dataset.zones(name))
    if not zones:
        raise RuntimeError(f'No zones matching "{name}"')
    return zones[index]


#-----------------------------------------------------------------------
# Layout Manipulation
#-----------------------------------------------------------------------
def add_page(**args):
    ''' Add and configure a new page in the layout '''
    arg_types = {
        'name':     str,
        'position': _Position,
    }
    page = tp.add_page()
    set_attributes(page, args, arg_types)
    return page

def add_frame(page=None, **args):
    ''' Add and configure a new frame on the page '''
    arg_types = {
        'border_thickness': float,
        'height':           float,
        'name':             str,
        'plot_type':        _PlotType,
        'position':         _Position,
        'show_border':      bool,
        'show_header':      bool,
        'transparent':      bool,
        'width':            float,
    }
    if not page:
        page = tp.active_page()
    frame = page.add_frame()
    set_attributes(frame, args , arg_types)
    return frame

def add_xylinemap(plot=None, **args):
    ''' Add and configure a linmap to an XYLinePlot '''

    linemap_types = {
        'name':             str,
        'show':             bool,
        'show_in_legend':   bool,
        'x_axis_index':     int,
        'x_variable':       _Variable,
        'x_variable_index': int,
        'y_axis_index':     int,
        'y_variable':       _Variable,
        'y_variable_index': int,
        'zone':             _Zone,
        'zone_index':       int,
    }
    line_types = {
        'color':            _Color,
        'line_pattern':     _Pattern,
        'line_thickness':   float,
        'pattern_length':   float,
        'show':             bool,
    }
    symbols_types = {
        'color':            _Color,
        'fill_color':       _Color,
        'fill_mode':        _FillMode,
        'line_thickness':   float,
        'show':             bool,
        'size':             float,
        'step':             float,
        'step_mode':        _StepMode,
        # shape... must be handled special (polymophic)
    }

    # PyTecplot has no way to instantiate line or symbols types,
    # so need to manually assign attributes.
    line_args    = args.pop('line',{})
    symbols_args = args.pop('symbols',{})
    shape_arg    = _SymbolShape(symbols_args.pop('shape','Circle'))

    # Set all the attributes
    if not plot:
        plot = tp.active_frame().plot(tpc.PlotType.XYLine)
        plot.activate()
    linemap = plot.add_linemap()
    set_attributes(linemap, args, linemap_types)
    set_attributes(linemap.line, line_args, line_types)
    set_attributes(linemap.symbols, symbols_args, symbols_types)
    linemap.symbols.symbol().shape = shape_arg

    return linemap

def configure_xylineplot(plot=None, **args):
    ''' Configure an XYLinePlot '''
    plot.show_lines   = args.get('show_lines',   True)
    plot.show_symbols = args.get('show_symbols', False)
    plot.legend.show  = args.get('show_legend',  True)
    view = args.get('view')
    if view:
        view_action = {
            'adjust_to_nice':   plot.view.adjust_to_nice,
            'center':           plot.view.center,
            'fit':              plot.view.fit,
            'fit_data':         plot.view.fit_data,
            'fit_to_nice':      plot.view.fit_to_nice,
        }
        view_action[view]()

def configure_xylineaxis(axis, **args):
    ''' Configure an XYLineAxis '''
    arg_types = {
        'log_scale':        bool,
        'max':              float,
        'min':              float,
        'reverse':          bool,
        'show':             bool,
    }
    title = args.pop('title')
    if title:
        axis.title.text = title
        axis.title.title_mode = tpc.AxisTitleMode.UseText
    set_attributes(axis, args, arg_types)


#-----------------------------------------------------------------------
# Main Entry Point
#-----------------------------------------------------------------------
def make_layout(datafiles, page_specs, equations=None):
    ''' Clear and configure a layout from a dict-like data structure

        This function enables construction of a Tecplot layout from
        dict-like datastructures, e.g. a YAML document. This function
        manipulates the state of the Tecplot runtime, and will clear
        any existing plots that have been defined.

        Arguments:
            datafiles    List(str) of datafile names to be loaded
            page_spec    List(dict) of properties defining each page
            equations    List(str) of equations applied to the dataset

        Returns:
            None

    '''

    # Load and pre-process data
    tp.new_layout()
    tp.data.load_tecplot(datafiles)
    if equations:
        tp.data.operate.execute_equation('\n'.join(equations))
    default_page = tp.active_page()

    # Construct the layout
    for page_spec in page_specs:
        frame_specs = page_spec.pop('frames')
        page = add_page(**page_spec)
        default_frame = page.active_frame()
        for frame_spec in frame_specs:
            lmap_specs = frame_spec.pop('linemaps',{})
            axis_specs = frame_spec.pop('axes',{})
            plot_spec  = frame_spec.pop('plot',{})
            frame = add_frame(**frame_spec)
            xyplot = frame.plot(tpc.PlotType.XYLine)
            xyplot.activate()
            xyplot.delete_linemaps()
            for lmap_spec in lmap_specs:
                add_xylinemap(xyplot, **lmap_spec)
            for axis_name,axis_spec in axis_specs.items():
                name,index = parse_selector(axis_name)
                if name.startswith('x'):
                    configure_xylineaxis(xyplot.axes.x_axis(index), **axis_spec)
                if name.startswith('y'):
                    configure_xylineaxis(xyplot.axes.y_axis(index), **axis_spec)
            configure_xylineplot(xyplot,**plot_spec)
        page.delete_frame(default_frame)
    tp.delete_page(default_page)
