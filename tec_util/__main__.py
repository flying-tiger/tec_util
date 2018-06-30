import argparse
import logging
import os
import sys
import tec_util
logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


#-------------------------------------------------------------------------------
# Subcommmands
#-------------------------------------------------------------------------------
def diff(args):
    ''' Compute delta between two solution files '''
    tec_util.difference_datasets(
        args.datafile_new,
        args.datafile_old,
        args.datafile_out,
        zone_pattern = args.zone_pattern,
        var_pattern = args.var_pattern,
        nskip = args.nskip,
    )

def export(args):
    ''' Export all pages in a layout to [prefix]<page.name>.png '''
    import tecplot as tp
    tp.layout.load_layout(args.layout_file)
    tec_util.export_pages(
        args.output_dir,
        args.prefix,
        args.width,
        args.supersample,
        args.yvar,
        args.cvar,
        args.rescale,
        args.num_contour,
    )

def info(args):
    ''' Print summary information about a dataset '''
    import tecplot as tp
    from tecplot.constant import ZoneType as zt
    dataset = tp.data.load_tecplot(args.datafile_in)
    has_times = hasattr(dataset, 'num_solution_times') # Missing in early versions of pytecplot

    # Determine width for pretty printed data
    zone_name_length = max([len(z.name) for z in dataset.zones()])
    var_name_length  = max([len(v.name) for v in dataset.variables()])
    col_width = max([zone_name_length+6, var_name_length+6, 15]) + 4

    print("\nDataset Info:")
    print((
        " {1:{0}s} {df}\n"
        " {2:{0}s} {ds.title}\n"
        " {3:{0}s} {ds.num_zones}\n"
        " {4:{0}s} {ds.num_variables}"
        ).format(
            col_width, 'Filename:', 'Title:', 'Num. Zones:', 'Num. Variables:',
            df=args.datafile_in, ds=dataset
    ))
    if has_times:
        print(" {1:{0}s} {ds.num_solution_times}".format(col_width, 'Num. Timepoints:', ds=dataset))

    print("\nZone Info:")
    for zone in dataset.zones():
        leader = "[{z.index:^3d}] {z.name}".format(z=zone)
        if zone.zone_type == zt.Ordered:
            line = " {1:{0}s} {z.zone_type.name} Zone, Strand={z.strand}, Dimensions={z.dimensions}"
        else:
            line = " {1:{0}s} {z.zone_type.name} Zone, Strand={z.strand}, NElements={z.num_elements}, NFaces={z.num_faces}"
        print(line.format(col_width, leader, z=zone))

    print("\nVariable Info:")
    for var in dataset.variables():
        vmin,vmax = float('inf'), -float('inf')
        for i in range(var.num_zones):
            vmin = min(vmin, var.values(i).min)
            vmax = max(vmax, var.values(i).max)
        leader = "[{v.index:^3d}] {v.name}".format(v=var)
        print(" {1:{0}s} Min= {2:+12.5e}, Max= {3:+12.5e}".format(col_width, leader, vmin, vmax))

    print("\nTimepoint Info:")
    if has_times and dataset.num_solution_times > 0:
        for i, time in enumerate(dataset.solution_times):
            print(" [{:^3d}] {}".format(i, time))
    else:
        print(" None")
    print()

def interp(args):
    ''' Inverse-distance interpolation of dataset onto a new grid. '''
    tec_util.interpolate_dataset(
        args.datafile_src,
        args.datafile_tgt,
        args.datafile_out,
    )

def slice(args):
    ''' Extract slices from dataset of surfaces zones. '''
    tec_util.slice_surfaces(
        args.slice_file,
        args.datafile_in,
        args.datafile_out
    )

def stats(args):
    ''' Extract zone max/min/averages for each variable. '''
    stats = tec_util.compute_statistics(args.datafile_in, args.variables)

    columns = ['Variable,', 'ZoneID', 'Zone,', 'Min', 'Max', 'Mean']
    var_width  = len(columns[0])
    zone_width = len(columns[2])
    for var_name, var_stats in stats.items():
        var_width = max(var_width, len(var_name)+1)
        for zone in var_stats:
            zone_width = max(zone_width, len(zone.name)+1)
    print(
        '{:{var_width}s} {:4s}, {:{zone_width}s} {:>15s}, {:>15s}, {:>15s}'
        .format(*columns, var_width=var_width, zone_width=zone_width),
    )
    for var_name, var_stats in stats.items():
        for i, zone in enumerate(var_stats):
            print(
                '{:{var_width}s} {:7s} {:{zone_width}s} {:15.6e}, {:15.6e}, {:15.6e}'
                .format(
                    var_name+',', str(i)+',', zone.name+',', zone.min, zone.max, zone.mean,
                    var_width=var_width, zone_width=zone_width,
                )
            )
    print()

def rename_vars(args):
    ''' Rename variables within the dataset. '''
    name_map = dict([np.split('=') for np in args.name_pairs])
    tec_util.rename_variables(
        args.datafile_in,
        args.datafile_out,
        name_map
    )

def rename_zones(args):
    ''' Rename variables within the dataset. '''
    name_map = dict([np.split('=') for np in args.name_pairs])
    tec_util.rename_zones(
        args.datafile_in,
        args.datafile_out,
        name_map
    )

def revolve(args):
    ''' Create a 3D surface|volume by revoling a 2D curve|plane '''

    # Combine all vector-spec dicts into one dict
    vectors = {}
    if args.vector:
        for v in args.vector:
            vectors.update(v)

    # Dispacth to library
    tec_util.revolve_dataset(
        args.datafile_in,
        args.datafile_out,
        radial_coord = args.radial_coord,
        planes       = args.num_planes,
        angle        = args.angle,
        vector_vars  = vectors,
    )

def to_ascii(args):
    ''' Convert a Tecplot datafile to ascii format '''
    import tecplot as tp
    dataset = tp.data.load_tecplot(args.datafile_in)
    tp.data.save_tecplot_ascii(args.datafile_out, dataset=dataset)

def to_plt(args):
    ''' Convert a Tecplot datafile to binary (plt) format '''
    import tecplot as tp
    dataset = tp.data.load_tecplot(args.datafile_in)
    tp.data.save_tecplot_plt(args.datafile_out, dataset=dataset)


#-------------------------------------------------------------------------------
# Subcommand Parser Configurators
#-------------------------------------------------------------------------------
def configure_diff_parser(parser):
    parser.add_argument(
        'datafile_new',
        help = "file to be differenced",
    )
    parser.add_argument(
        'datafile_old',
        help = "file to be used as baseline",
    )
    parser.add_argument(
        '-o', '--datafile_out',
        help = "file where differences are saved (def: diff.plt)",
        nargs = "?",
        default = "diff.plt",
    )
    parser.add_argument(
        '-z', '--zone_pattern',
        help = "Glob pattern for filtering zones (def: '*')",
        default = "*",
    )
    parser.add_argument(
        '-v', '--var_pattern',
        help = "Glob pattern for filtering variables (def: '*')",
        default = "*",
    )
    parser.add_argument(
        '--nskip',
        help = (
            "Number of variables at beginning of the dataset that "
            "are not differenced (preserves grid coordinates, def: 3)"
        ),
        type = int,
        default = 3,
    )

def configure_export_parser(parser):
    parser.add_argument(
        "layout_file",
        help = "path to layout file to be processed"
    )
    parser.add_argument(
        "--output_dir", "-o",
        help = "location where PNG files will be saved (def: '.')",
        nargs = "?",
        default = ".",
    )
    parser.add_argument(
        "--prefix",
        help = "string added to page.name to create filename (def: '')",
        default = "",
    )
    parser.add_argument(
        "--width", "-w",
        help = "width of exported figures in pixels (def: 600)",
        default = 600,
        type = int,
    )
    parser.add_argument(
        "--supersample", "-s",
        help = "supersampling level used during export (def: 2)",
        metavar = "SS",
        default = 2,
        type = int,
    )
    parser.add_argument(
        "--yvar",
        help = "Set y_variable used for linemaps plotted on 1st y-axis",
        default = None,
    )
    parser.add_argument(
        "--cvar",
        help = "variable used for the 1st contour group",
        default = None,
    )
    parser.add_argument(
        "--rescale",
        help = "rescales colormaps and x,y axes to fit data (def: false)",
        default = False,
        action = 'store_true',
    )
    parser.add_argument(
        "--num_contour",
        help = "number of contour levels when rescaling (def: 21)",
        metavar = "N",
        default = 21,
        type = int,
    )

def configure_info_parser(parser):
    parser.add_argument(
        "datafile_in",
        help = "file to print metadata for",
    )

def configure_interp_parser(parser):
    parser.add_argument(
        'datafile_src',
        help = "dataset to be interpolated",
    )
    parser.add_argument(
        'datafile_tgt',
        help = "target grid to be populated",
    )
    parser.add_argument(
        '-o', '--datafile_out',
        help = "file where differences are saved (def: interp.plt)",
        nargs = "?",
        default = "interp.plt",
    )

def configure_rename_vars_parser(parser):
    parser.add_argument(
        "datafile_in",
        help = "input dataset",
    )
    parser.add_argument(
        "name_pairs",
        metavar = "name_pair",
        help = "rename specifier <old_name>=<new_name>",
        nargs = "+",
    )
    parser.add_argument(
        "-o", "--datafile_out",
        help = "file where renamed dataset is saved (def: renamed.plt)",
        default = "renamed.plt",
    )

def configure_rename_zones_parser(parser):
    parser.add_argument(
        "datafile_in",
        help = "input dataset",
    )
    parser.add_argument(
        "name_pairs",
        metavar = "name_pair",
        help = "rename specifier <old_name>=<new_name>",
        nargs = "+",
    )
    parser.add_argument(
        "-o", "--datafile_out",
        help = "file where renamed dataset is saved (def: renamed.plt)",
        default = "renamed.plt",
    )

def configure_revolve_parser(parser):
    def coord_spec(arg):
        ''' Helper for parsing radial_coord arugment. '''
        name_in,*names_out = arg.split(':')
        if not names_out:
            return name_in.strip()
        else:
            return vector_spec(arg)

    def vector_spec(arg):
        ''' Helper function for parsing vector specifiers from command line '''
        name_in,*names_out = arg.split(':')
        name_in = name_in.strip()
        if not names_out:
            return { name_in : [name_in + '_cos', name_in + '_sin']}
        else:
            names_out = names_out[0].split(',')
            assert len(names_out) == 2, \
                   f'ERROR: Bad vector argument "{arg}". Rename-part of spec must be' \
                   'a comma separated pair of strings'
            return { name_in : names_out }

    parser.add_argument(
        "datafile_in",
        help = "input dataset",
    )
    parser.add_argument(
        "-o", "--datafile_out",
        help = "file where revolved dataset is saved (def: revolve.plt)",
        default = "revolve.plt",
    )
    parser.add_argument(
        "-n", "--num_planes",
        help = "number of planes created by revolution (def: 37)",
        type = int,
        default = 37,
    )
    parser.add_argument(
        "-a", "--angle",
        help = "angle of revolution in degrees (def: 180)",
        type = float,
        default = 180.0,
    )
    parser.add_argument(
        "-r", "--radial_coord",
        help = "variable used as radial coordinate (def: 2nd var in dataset)",
        type = coord_spec,
        default = None
    )
    parser.add_argument(
        "-v", "--vector",
        help = "variable to be revolved as a vector, v->(v*cos(t),v*sin(t))",
        type = vector_spec,
        action = 'append',
        default = None
    )

def configure_slice_parser(parser):
    parser.add_argument(
        "slice_file",
        help = "file defining the slices to be generated",
    )
    parser.add_argument(
        "datafile_in",
        help = "file with surface data to be processed",
    )
    parser.add_argument(
        "-o", "--datafile_out",
        help = "file where extracted slices will be saved (def: slices.plt)",
        default = "slices.plt",
    )

def configure_stats_parser(parser):
    parser.add_argument(
        "datafile_in",
        help = "file to be analyzed",
    )
    parser.add_argument(
        "variables",
        help = "variables to be analyzed (supports globbing).",
        nargs = "*",
        default = None,
    )

def configure_to_ascii_parser(parser):
    parser.add_argument(
        "datafile_in",
        help = "file to be converted",
    )
    parser.add_argument(
        "-o", "--datafile_out",
        help = "file where ascii data is saved (def: dataset.dat)",
        default = "dataset.dat",
    )

def configure_to_plt_parser(parser):
    parser.add_argument(
        "datafile_in",
        help = "file to be converted",
    )
    parser.add_argument(
        "-o", "--datafile_out",
        help = "file where binary data is saved (def: dataset.plt)",
        default = "dataset.plt",
    )


#-------------------------------------------------------------------------------
# Main Program
#-------------------------------------------------------------------------------
def build_parser():
    ''' Construct the command line argument parser '''

    # Main parser
    parser = argparse.ArgumentParser(
        prog = "tec_util",
        description = "Utilities for working with Tecplot data files.",
    )
    parser.add_argument(
        '-v', '--verbose',
        help = 'show detailed output log',
        action = 'store_const',
        dest = 'loglevel',
        const = logging.INFO,
        default = logging.WARNING,
    )
    parser.add_argument(
        '-d', '--debug',
        help = 'show all debugging output',
        action = 'store_const',
        dest = 'loglevel',
        const = logging.DEBUG,
    )
    subparsers = parser.add_subparsers(
        metavar = 'cmd',
        help = 'Subcommand to execute',
    )

    # Subcommand parsers
    cmds = {
        # name            function       parser
        'diff':         ( diff,          configure_diff_parser         ),
        'export':       ( export,        configure_export_parser       ),
        'info':         ( info,          configure_info_parser         ),
        'interp':       ( interp,        configure_interp_parser       ),
        'slice':        ( slice,         configure_slice_parser        ),
        'stats':        ( stats,         configure_stats_parser        ),
        'rename_vars':  ( rename_vars,   configure_rename_vars_parser  ),
        'rename_zones': ( rename_zones,  configure_rename_zones_parser ),
        'revolve':      ( revolve,       configure_revolve_parser      ),
        'to_ascii':     ( to_ascii,      configure_to_ascii_parser     ),
        'to_plt':       ( to_plt,        configure_to_plt_parser       ),
    }
    for name, (action, configure_func) in cmds.items():
        sp = subparsers.add_parser(
            name,
            help = action.__doc__,
            description = action.__doc__,
        )
        configure_func(sp)
        sp.set_defaults(func = action)

    return parser

def main(args):
    parser = build_parser()
    args = parser.parse_args(args)
    logging.getLogger('tec_util').setLevel(args.loglevel)
    if "func" in args:
        args.func(args)
    else:
        parser.print_help()
    if os.path.exists("batch.log"):
        os.remove("batch.log")

if __name__ == '__main__':
    main(sys.argv[1:])

