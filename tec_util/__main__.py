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
    columns = ['Variable,','Zone','Min', 'Max', 'Mean']
    width = max(len(columns[0]), max([len(k) for k in stats])+1)
    print('{:{width}s} {:4s}, {:>15s}, {:>15s}, {:>15s}'
          .format(*columns, width=width))
    for vname, zone_stats in stats.items():
        for i, stats in enumerate(zone_stats):
            print('{:{width}s} {:4d}, {:15.6e}, {:15.6e}, {:15.6e}'
                  .format(vname+',', i, stats.min, stats.max, stats.mean, width=width))
    print()

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
        "datafile_out",
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
        "output_dir",
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
        help = "rescales colormaps and y-axes to fit data (def: false)",
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

def configure_slice_parser(parser):
    parser.add_argument(
        "slice_file",
        help = "file defining the slices to be generated"
    )
    parser.add_argument(
        "datafile_in",
        help = "file with surface data to be processed",
    )
    parser.add_argument(
        "datafile_out",
        help = "file where extracted slices will be saved (def: slices.plt)",
        nargs = "?",
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
        "datafile_out",
        help = "file where ascii data is saved (def: dataset.dat)",
        nargs = "?",
        default = "dataset.dat",
    )

def configure_to_plt_parser(parser):
    parser.add_argument(
        "datafile_in",
        help = "file to be converted",
    )
    parser.add_argument(
        "datafile_out",
        help = "file where binary data is saved (def: dataset.plt)",
        nargs = "?",
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
        # name        function   parser
        'diff':     ( diff,      configure_diff_parser     ),
        'export':   ( export,    configure_export_parser   ),
        'info':     ( info,      configure_info_parser     ),
        'slice':    ( slice,     configure_slice_parser    ),
        'stats':    ( stats,     configure_stats_parser    ),
        'to_ascii': ( to_ascii,  configure_to_ascii_parser ),
        'to_plt':   ( to_plt,    configure_to_plt_parser   ),
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

def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.getLogger('tec_util').setLevel(args.loglevel)
    if "func" in args:
        args.func(args)
    else:
        parser.print_help()
    if os.path.exists("batch.log"):
        os.remove("batch.log")

if __name__ == '__main__':
    main()

