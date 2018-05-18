import collections
import itertools
import logging
import math
import os
import sys
import tempfile
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from statistics import mean
# import tecplot  (deferred to function scope to minimize load time)

LOG = logging.getLogger(__name__)


#-----------------------------------------------------------------------
# Helper Functions
#-----------------------------------------------------------------------
def rescale_frame(frame, num_contour):
    ''' Rescale 1st colormap for 2D and 3D plots, 1st xy-axes for XY plots '''
    import tecplot.constant as tpc
    plot = frame.plot()
    if (frame.plot_type == tpc.PlotType.Cartesian3D or  \
       frame.plot_type == tpc.PlotType.Cartesian2D) and \
       plot.show_contour == True:
        LOG.debug("Rescale first contour group")
        levels = plot.contour(0).levels
        cfilt = plot.contour(0).colormap_filter
        levels.reset_to_nice(num_contour)
        cfilt.continuous_max = max(levels)
        cfilt.continuous_min = min(levels)
    elif frame.plot_type == tpc.PlotType.XYLine:
        LOG.debug("Rescale first Y axis")
        plot.axes.y_axis(0).fit_range_to_nice()
        LOG.debug("Rescale first X axis")
        plot.axes.x_axis(0).fit_range_to_nice()

def set_linemap_yvariable(frame, yvar):
    ''' Set y_variable for all linemaps using the 1st y-axis '''
    import tecplot.constant as tpc
    if frame.plot_type == tpc.PlotType.XYLine:
        for i,lmap in enumerate(frame.plot().linemaps()):
            LOG.debug("Setting y_variable for linemap %d", i)
            if lmap.y_axis_index == 0:
                lmap.y_variable = frame.dataset.variable(yvar)

def set_contour_variable(frame, cvar):
    ''' Set variable used to color the first contour group '''
    import tecplot.constant as tpc
    plot = frame.plot()
    if (frame.plot_type == tpc.PlotType.Cartesian3D or  \
       frame.plot_type == tpc.PlotType.Cartesian2D) and \
       plot.show_contour == True:
        LOG.debug("Setting variable for first contour group")
        plot.contour(0).variable = frame.dataset.variable(cvar)

@contextmanager
def temp_frame():
    ''' Create/deletes a temporary frame on the current layout page.
    '''
    import tecplot
    page  = tecplot.active_page()
    frame = page.add_frame()
    yield frame
    page.delete_frame(frame)

def write_dataset(filename, dataset, **kwargs):
    ''' Writes dataset as ASCII or PLT depending on extension '''
    import tecplot as tp
    LOG.info("Write dataset %s", filename)
    ext = os.path.splitext(filename)[1]
    if ext == ".dat":
        tp.data.save_tecplot_ascii(filename, dataset=dataset, **kwargs)
    else:
        tp.data.save_tecplot_plt(filename, dataset=dataset, **kwargs)


#-----------------------------------------------------------------------
# API Functions
#-----------------------------------------------------------------------
def compute_statistics(datafile_in, variable_patterns=None):
    ''' Compute min/max/mean for each variable/zone combination

    Arguments:
        datafile_in        [str]  Path of Tecplot datafile
        variable_patterns  [list(str)] Names of variable to be analyzed.
                           Wildcard patterns are allowed.

    Returns:
        stats_info         [dict(list(stats_tuple))] Data structure with
                           max/min/mean for every variable/zone combination
                           e.g. stats_info[var_name][zone_id].max
    '''
    import tecplot as tp
    import tecplot.constant as tpc
    with temp_frame() as frame:

        # Load the dataset
        LOG.info("Load dataset %s", datafile_in)
        dataset = tp.data.load_tecplot(
            datafile_in,
            frame = frame,
            initial_plot_type = tpc.PlotType.Cartesian3D
        )

        # Get all variables matching given patterns
        if variable_patterns:
            variables = {}
            for pattern in variable_patterns:
                for var in dataset.variables(pattern):
                    variables[var.name] = var
            variables = variables.values()
        else:
            variables = list(dataset.variables())
        LOG.info("Generating statisitics for: %s", ' '.join([v.name for v in variables]))

        # Compute per-zone statistics
        var_stats = {}
        stats_tuple = collections.namedtuple('ZoneStats',['name','max','min','mean'])
        for var in variables:
            zone_stats = []
            for zone in dataset.zones():
                data = dataset.variable(var.index).values(zone.index)
                zone_stats.append(stats_tuple(zone.name, data.max, data.min, mean(data[:])))
            var_stats[var.name] = zone_stats

    return var_stats

def difference_datasets(datafile_new, datafile_old, datafile_out, zone_pattern="*", var_pattern="*", nskip=3):
    ''' Compute variable-by-variable difference between datasets.

        INPUTS:
            datafile_new    Path to datafile to be differenced
            datafile_old    Path to datafile to use a baseline
            datafile_out    Path where datafile of differences is saved
            zone_pattern    Glob pattern for selecting zones to difference (def: "*")
            var_pattern     Glob pattern for selecting variables to difference (def: "*")
            nskip           Number of variables at start of file to skip (def:3)

        OUTPUTS:
            none
    '''
    import tecplot as tp
    import tecplot.constant as tpc
    try:
        from numpy import subtract
    except:
        def subtract(x_arr,y_arr):
            return [x-y for x,y in zip(a_arr,y_arr)]

    with temp_frame() as frame_new, temp_frame() as frame_old:

        # Load datasets
        LOG.info("Load new dataset from %s", datafile_new)
        data_new = tp.data.load_tecplot(datafile_new, frame = frame_new)
        LOG.info("Load old dataset from %s", datafile_old)
        data_old = tp.data.load_tecplot(datafile_old, frame = frame_old)

        # Get variable information
        var_new = list(data_new.variables(var_pattern))
        var_old = list(data_old.variables(var_pattern))
        if len(var_new) != len(var_old):
            message = (
                "The number of variables matching the glob pattern "
                "'{}' in datafile_new ({}) does not match the number "
                "in datafile_old ({})."
            ).format(var_pattern, len(var_new), len(var_old))
            LOG.error(message)
            raise RuntimeError(message)
        for i, (vnew, vold) in enumerate(zip(var_new, var_old)):
            if vnew.name != vold.name:
                LOG.warning(
                    "Variable pair %d has mismatching names: %s != %s",
                    i, vnew.name, vold.name,
                )

        # Get zone information
        zone_new = list(data_new.zones(zone_pattern))
        zone_old = list(data_old.zones(zone_pattern))
        if len(zone_new) != len(zone_old):
            message = (
                "The number of zones matching the glob pattern "
                "'{}' in datafile_new ({}) does not match the number "
                "in datafile_old ({})."
            ).format(zone_pattern, len(zone_new), len(zone_old))
            LOG.error(message)
            raise RuntimeError(message)
        for i, (znew, zold) in enumerate(zip(zone_new, zone_old)):
            if znew.name != zold.name:
                LOG.warning(
                    "Zone pair %d has mismatching names: %s != %s",
                    i, znew.name, zold.name,
                )

        # Compute delta new - old. Deltas get appended to data_new.
        LOG.info("Compute dataset differences (new - old).")
        initial_num_vars = data_new.num_variables
        for i, (vnew, vold) in enumerate(zip(var_new, var_old)):
            if vnew.index < nskip or vold.index < nskip:
                LOG.debug("Skipping variable pair %d; index less than nskip", i)
                continue
            delta = data_new.add_variable("delta_" + vnew.name)
            for znew, zold in zip(zone_new, zone_old):
                try:
                    delta.values(znew.index)[:] = subtract(
                        vnew.values(znew.index)[:],
                        vold.values(zold.index)[:],
                    )
                except:
                    LOG.exception(
                        'Error while computing delta "%s" for zones "%s" and "%s". Setting to NaN.',
                        zold.name, znew.name,
                    )
                    delta.values(znew.index)[:] = [math.nan] * len(delta.values(znew.index))

        # Save results
        vars_to_save = itertools.chain(range(nskip),range(initial_num_vars, data_new.num_variables))
        write_dataset(datafile_out, data_new, variables=vars_to_save, zones=zone_new)

def export_pages(output_dir, prefix='', width=600, supersample=2,
                 yvar=None, cvar=None, rescale=False, num_contour=21):
    ''' Export all pages in the current layout to <page_name>.png '''
    import tecplot as tp
    import tecplot.constant as tpc
    os.makedirs(output_dir, exist_ok=True)
    for page in tp.pages():
        page.activate()
        for frame in page.frames():
            LOG.debug("Pre-process frame %s on page %s", frame.name, page.name)
            if yvar:
                set_linemap_yvariable(frame, yvar)
            if cvar:
                set_contour_variable(frame, cvar)
            if rescale:
                rescale_frame(frame, num_contour)
        outfile = os.path.join(output_dir, prefix + page.name + ".png")
        LOG.info("Export page %s to %s", page.name, outfile)
        tp.export.save_png(
            outfile, width,
            region = tpc.ExportRegion.AllFrames,
            supersample = supersample
        )

def interpolate_dataset(datafile_src, datafile_tgt, datafile_out):
    ''' Interpolate variables from one dataset onto another (3D only)

        INPUTS:
            datafile_src    Path to datafile to be interpolated
            datafile_tgt    Path to datafile with interpolation coordintes
            datafile_out    Path where datafile with interpolated data is saved

        OUTPUTS:
            none
    '''
    import tecplot as tp
    import tecplot.constant as tpc
    with temp_frame() as frame:

        # Load datasets
        LOG.info("Load source dataset from %s", datafile_src)
        data = tp.data.load_tecplot(
            datafile_src,
            frame = frame,
            initial_plot_type = tpc.PlotType.Cartesian3D,
        )
        nzone_src = data.num_zones
        LOG.info("Load target dataset from %s", datafile_tgt)
        tp.data.load_tecplot(
            datafile_tgt,
            frame = frame,
            read_data_option = tpc.ReadDataOption.Append,
        )

        # Perform interpolation
        src_zones = [data.zone(i) for i in range(nzone_src)]
        tgt_zones = [data.zone(i) for i in range(nzone_src, data.num_zones)]
        for zone in tgt_zones:
            tp.data.operate.interpolate_inverse_distance(
                destination_zone = zone,
                source_zones = src_zones,
            )

        # Save results
        write_dataset(datafile_out, data, zones=tgt_zones)

def rename_variables(datafile_in, datafile_out, name_map):
    ''' Rename variables in a dataset '''
    import tecplot as tp
    import tecplot.constant as tpc
    with temp_frame() as frame:

        # Create frame to hold data. This modifies the global state of
        # the tecplot module and must be undone in the "finally" block.
        frame = tp.active_page().add_frame()

        # Load the dataset
        LOG.info("Load dataset %s", datafile_in)
        dataset = tp.data.load_tecplot(
            datafile_in,
            frame = frame,
            initial_plot_type = tpc.PlotType.Cartesian3D
        )

        # Rename the variables
        for old_name, new_name in name_map.items():
            var = dataset.variable(old_name)
            var.name = new_name
            LOG.info("Rename %d-th variable '%s' to '%s'", var.index, old_name, new_name)

        # Save results
        write_dataset(datafile_out, dataset)

def rename_zones(datafile_in, datafile_out, name_map):
    ''' Rename zones in a dataset '''
    import tecplot as tp
    import tecplot.constant as tpc
    with temp_frame() as frame:

        # Load the dataset
        LOG.info("Load dataset %s", datafile_in)
        dataset = tp.data.load_tecplot(
            datafile_in,
            frame = frame,
            initial_plot_type = tpc.PlotType.Cartesian3D
        )

        # Rename the variables
        for old_name, new_name in name_map.items():
            zone = dataset.zone(old_name)
            zone.name = new_name
            LOG.info("Rename %d-th zone '%s' to '%s'", zone.index, old_name, new_name)

        # Save results
        write_dataset(datafile_out, dataset)

def slice_surfaces(slice_file, datafile_in, datafile_out):
    ''' Extract slice zones from a datafile of surface zones.

        INPUTS:
            slice_file
                Path to a python module that defines a list of tuples called
                "slices". The elements of each tuple are:
                    [0] Name of the slice (string)
                    [1] Origin of the slice plane (3-tuple of floats)
                    [2] Normal vector of the slice plane (3-tuple of floats)
                    [3] Indices of surface zones to be sliced (list of ints)

            datafile_in
                Path to Tecplot dataset with surface zone to slice

            datafile_out
                Path where slice data will be written. If the filename has the
                extension ".dat", the data will be written in ASCII format.
                Otherwise, binary format will be used.

        OUPUTS:
            none
    '''
    import tecplot as tp
    import tecplot.constant as tpc

    # Load slice definition file as "config" module
    # This is based on https://stackoverflow.com/questions/67631
    LOG.info("Load slice definition from %s", slice_file)
    sys.dont_write_bytecode = True # So we don't clutter users workspace
    config = SourceFileLoader("config", slice_file).load_module()
    sys.dont_write_bytecode = False

    try:

        # Create frame to hold data. This modifies the global state of
        # the tecplot module and must be undone in the "finally" block.
        frame = tp.active_page().add_frame()

        # Load and slice the dataset
        LOG.info("Load dataset %s", datafile_in)
        dataset = tp.data.load_tecplot(
            datafile_in,
            frame = frame,
            initial_plot_type = tpc.PlotType.Cartesian3D
        )
        slice_zones = []
        for slice_definition in config.slices:
            name, origin, normal, zones = slice_definition
            if isinstance(zones, str):
                if zones == "all":
                    zones = range(dataset.num_zones)
                else:
                    raise RuntimeError("String '%s' is not a valid zone specifier" % zones)
            LOG.info("Extract slice '%s'", name)
            frame.active_zones(zones)
            zone = tp.data.extract.extract_slice(
                origin  = origin,
                normal  = normal,
                source  = tpc.SliceSource.SurfaceZones,
                dataset = dataset,
            )
            zone.name = name
            slice_zones.append(zone)

        # Save results
        write_dataset(datafile_out, dataset, zones=slice_zones)

    finally:
        # Restore global state
        tp.active_page().delete_frame(frame)


