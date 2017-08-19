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
def slice(args):
    ''' Extract slices from dataset of surfaces zones. '''
    tec_util.slice_surfaces(
        args.slice_file,
        args.datafile_in,
        args.datafile_out
    )

def export(args):
    ''' Export all pages in a layout to [prefix]<page.name>.png '''
    tec_util.export_pages(
        args.layout_file,
        args.output_dir,
        args.prefix,
        args.width,
        args.supersample,
        args.yvar,
        args.cvar,
        args.rescale,
        args.num_contour,
    )

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
# Main Program
#-------------------------------------------------------------------------------
def build_parser():
    ''' Construct the command line argument parser '''

    #---- Main parser ----
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

    #---- Slice parser ----
    slice_parser = subparsers.add_parser(
        'slice',
        help = slice.__doc__,
        description = slice.__doc__,
    )
    slice_parser.add_argument(
        "slice_file",
        help = "file defining the slices to be generated"
    )
    slice_parser.add_argument(
        "datafile_in",
        help = "file with surface data to be processed",
    )
    slice_parser.add_argument(
        "datafile_out",
        help = "file where extracted slices will be saved (def: slices.plt)",
        nargs = "?",
        default = "slices.plt",
    )
    slice_parser.set_defaults(func = slice)

    #---- Export parser ----
    export_parser = subparsers.add_parser(
        'export',
        help = export.__doc__,
        description = export.__doc__,
    )
    export_parser.add_argument(
        "layout_file",
        help = "path to layout file to be processed"
    )
    export_parser.add_argument(
        "output_dir",
        help = "location where PNG files will be saved (def: '.')",
        nargs = "?",
        default = ".",
    )
    export_parser.add_argument(
        "prefix",
        help = "string added to page.name to create filename (def: '')",
        nargs = "?",
        default = "",
    )
    export_parser.add_argument(
        "--width", "-w",
        help = "width of exported figures in pixels (def: 600)",
        default = 600,
        type = int,
    )
    export_parser.add_argument(
        "--supersample", "-s",
        help = "supersampling level used during export (def: 2)",
        metavar = "SS",
        default = 2,
        type = int,
    )
    export_parser.add_argument(
        "--yvar",
        help = "Set y_variable used for linemaps plotted on 1st y-axis",
        default = None,
    )
    export_parser.add_argument(
        "--cvar",
        help = "variable used for the 1st contour group",
        default = None,
    )
    export_parser.add_argument(
        "--rescale",
        help = "rescales colormaps and y-axes to fit data (def: false)",
        default = False,
        action = 'store_true',
    )
    export_parser.add_argument(
        "--num_contour",
        help = "number of contour levels when rescaling (def: 21)",
        metavar = "N",
        default = 21,
        type = int,
    )
    export_parser.set_defaults(func = export)

    #---- File difference parser ----
    diff_parser = subparsers.add_parser(
        'diff',
        help = diff.__doc__,
        description = diff.__doc__,
    )
    diff_parser.add_argument(
        'datafile_new',
        help = "file to be differenced",
    )
    diff_parser.add_argument(
        'datafile_old',
        help = "file to be used as baseline",
    )
    diff_parser.add_argument(
        "datafile_out",
        help = "file where differences are saved (def: diff.plt)",
        nargs = "?",
        default = "diff.plt",
    )
    diff_parser.add_argument(
        '-z', '--zone_pattern',
        help = "Glob pattern for filtering zones (def: '*')",
        default = "*",
    )
    diff_parser.add_argument(
        '-v', '--var_pattern',
        help = "Glob pattern for filtering variables (def: '*')",
        default = "*",
    )
    diff_parser.add_argument(
        '--nskip',
        help = (
            "Number of variables at beginning of the dataset that "
            "are not differenced (preserves grid coordinates, def: 3)"
        ),
        type = int,
        default = 3,
    )
    diff_parser.set_defaults(func = diff)

    #---- ASCII Converter ----
    ascii_parser = subparsers.add_parser(
        'to_ascii',
        help = to_ascii.__doc__,
        description = to_ascii.__doc__,
    )
    ascii_parser.add_argument(
        "datafile_in",
        help = "file to be converted",
    )
    ascii_parser.add_argument(
        "datafile_out",
        help = "file where ascii data is saved (def: dataset.dat)",
        nargs = "?",
        default = "dataset.dat",
    )
    ascii_parser.set_defaults(func = to_ascii)

    #---- PLT Converter ----
    plt_parser = subparsers.add_parser(
        'to_plt',
        help = to_plt.__doc__,
        description = to_plt.__doc__,
    )
    plt_parser.add_argument(
        "datafile_in",
        help = "file to be converted",
    )
    plt_parser.add_argument(
        "datafile_out",
        help = "file where binary data is saved (def: dataset.plt)",
        nargs = "?",
        default = "dataset.plt",
    )
    plt_parser.set_defaults(func = to_plt)

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

