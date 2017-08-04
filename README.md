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

### Install via pip
The simplest installation method is to use pip to install directly from GitHub:

    pip install git+git://github.com/flying-tiger/tec_util.git
    
This will install the master branch into your site-packages along with the 
latest version of PyTecplot from PyPI.

### Manual Install
Alternatively, you can manually clone and install the package:

    # Do this once 
    git clone <install_path>
    
    # Put this in your .bashrc or similar
    export TECUTIL_ROOT=<install_path>
    export PYTHONPATH="$TECUTIL_ROOT:$PYTHON_PATH"
    alias tec_util="python3 -m tec_util"

If you use [envrionment modules](http://modules.sourceforge.net/), a modulefile is 
provided that will perform the envrionment configuration. Simply create symlink to
the modulefile from somewhere on the module search path and load the module. For example,
to use the ~/privatemodules directory:

    # Do this once
    mkdir -p ~/privatemodules
    ln -s <path_to_repo>/modulefile ~/privatemodules/cmatrix

    # Put this in your .bashrc or similar
    module load use.own
    module load cmatrix

### Making Sure PyTecplot is Configured
Even if you do the automated install, chances are PyTecplot will require some additional
configuration of the envrionment. Full installation instructions are 
[here](http://www.tecplot.com/docs/pytecplot/install.html). When properly installed, you
should be able to do the following:

    >> python3 -c "import tecplot; print(tecplot.version.version)"
    0.8.1

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
API and rely on the user load the output file into their layout manually. This is
not ideal, and I may extend this API in the future, but it does what we need it
to do for now.


