import logging
import os
import sys
import tempfile
from importlib.machinery import SourceFileLoader
# import tecplot  (deferred to function scope to minimize load time)

LOG = logging.getLogger(__name__)

def rescale_frame(frame, num_contour):
    ''' Rescale 1st colormap for 2D and 3D plots, 1st y-axis for XY plots '''
    import tecplot.constant as tpc
    plot = frame.plot()
    if (frame.plot_type == tpc.PlotType.Cartesian3D or  \
       frame.plot_type == tpc.PlotType.Cartesian2D) and \
       plot.show_contour == True:
        LOG.debug("Rescale first contour group")
        plot.contour(0).levels.reset_to_nice(num_contour)
    elif frame.plot_type == tpc.PlotType.XYLine:
        LOG.debug("Rescale first Y axis")
        plot.axes.y_axis(0).fit_range_to_nice()

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
    if (frame.plot_type == tpc.PlotType.Cartesian3D or  \
       frame.plot_type == tpc.PlotType.Cartesian2D) and \
       plot.show_contour == True:
        LOG.debug("Setting variable for first contour group")
        plot.contour(0).variable = frame.dataset.variable(cvar)

def export_pages(layout_file,
                 output_dir,
                 prefix = '',
                 width = 600,
                 supersample = 2,
                 yvar = None,
                 cvar = None,
                 rescale=False,
                 num_contour=21):
    ''' Export all pages in a layout to <page_name>.png '''
    import tecplot as tp
    import tecplot.constant as tpc
    LOG.info("Load layout file %s", layout_file)
    tp.layout.load_layout(layout_file)
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

    # Load and slice the dataset
    LOG.info("Load dataset %s", datafile_in)
    frame = tp.active_page().add_frame()
    dataset = tp.data.load_tecplot(
        datafile_in,
        frame = frame,
        initial_plot_type = tpc.PlotType.Cartesian3D
    )
    slice_zones = []
    for slice_definition in config.slices:
        name, origin, normal, zones = slice_definition
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

    # Write the output
    LOG.info("Write dataset %s", datafile_out)
    ext = os.path.splitext(datafile_out)[1]
    if ext == ".dat":
        tp.data.save_tecplot_ascii(datafile_out, zones = slice_zones)
    else:
        tp.data.save_tecplot_plt(datafile_out, zones = slice_zones)

    # Cleanup
    tp.active_page().delete_frame(frame)

