# tec_util
Utilities for working with Tecplot datafiles, targeting Python and the command
line.


## Overview
Starting with the 2017 R1 release, Tecplot 360EX ships with a Python API that
largely eliminates the need for macro files. This software provides a Python
module and an associated set of command line bindings for several common
operations that I used to implement using macro files.


## Requirements
* Python 3.4+
* Tecplot 360EX 2017 R2+


## Install
Before installing this software, ensure you have the PyTecplot interface
installed and your envrionment properly configured; instructions are
[here](http://www.tecplot.com/docs/pytecplot/install.html). When properly
installed, you should be able to do the following:

    >> python3 -c "import tecplot; print(tecplot.version.version)"
    0.8.1

To install tec_util, a modulefile is provided (see
[envrionment modules](http://modules.sourceforge.net/)). Simply symlink this
file into your privatemodules directory and load as follows:

    # Do this once
    mkdir -p ~/privatemodules
    ln -s <path_to_repo>/modulefile ~/privatemodules/cmatrix

    # Put this in your .bashrc or similar
    module load use.own
    module load cmatrix

To install manually:

* Set and export TEC_UTIL_ROOT
* Add $TEC_UTIL_ROOT/bin to the search path
* Add $TEC_UTIL_ROOT/python to the PYTHONPATH


## Command-Line Useage

    tec_util --help                              # Command summary
    tec_util to_ascii infile [outfile]           # Convert datafile to ASCII format
    tec_util to_plt   infile [outfile]           # Convert datafile to PLT format
    tec_util slice    slices.py infile [outfile] # Extract slices from surface zones
    tec_util export   layout.lay [outdir]        # Export all pages in layout to png

## Python Useage
Currently the Python API consists of two functions that reside in the tec_util
module: export_pages and slices_surfaces. These functions follow a similar API
to their command line counterpats. Both subroutines require a file name as input
and generate a new datafile containing the output. I chose this approach because
returning a new, logically independent dataset from a function is not possible
without adding a new frame to the user's layout, which may be undesireable.
Therefore, we fall back to properly isolated, but a less efficient file-based
API and force the user load the output file into their layout manually. This is
not ideal, and I may extend this API in the future, but it does what we need it
to do for now.


