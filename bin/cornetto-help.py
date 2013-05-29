#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2008-2013 by 
# Erwin Marsi and Tilburg University


# This file is part of the Pycornetto package.

# Pycornetto is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# Pycornetto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
open Pycornetto documentation in a webbrowser
"""

__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'

import sys

try:
    import cornetto
except ImportError, inst:
    print >>sys.stderr, inst 
    print >>sys.stderr, "Did you properly install Pycornetto using 'setup.py install' ?"
    exit(1)    

import webbrowser
import os

from cornetto.argparse import ArgumentParser


parser = ArgumentParser(description=__doc__,
                        version="%(prog)s version " + __version__)

parser.add_argument("-l", "--location", default=False, action='store_true',
                    help='just show where the documention is located on your system')

args = parser.parse_args()

# note that we cannot rely on sys.prefix, because pycornetto may be installed
# in a non.standard location
docpath = os.path.join(os.path.dirname(cornetto.__file__),
                       "..", # skip cornetto package dir
                       "..", # skip site-packages
                       "..", # skip pythonx.x
                       "..", # skip lib, now are at what  is normally sys.prefix
                       "share", 
                       "pycornetto-" + __version__,
                       "doc",
                       "index.html")

docpath = os.path.normpath(docpath)


if not os.path.exists(docpath):
    print >>sys.stderr, "Error: expected to find documentation under", docpath
    print >>sys.stderr, "Did you properly install Pycornetto using 'setup.py install' ?"
    exit(1)
elif args.location:
    print docpath
else:
    webbrowser.open(docpath)
    
