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
simple server providing access to the Cornetto Database through XML-RPC

WARNING: this server is not secure and should not run on open networks!
"""

# TODO:
# - forking/threading


__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'

from sys import exit
from cornetto.argparse import ArgumentParser, RawDescriptionHelpFormatter
from cornetto.server import start_server


parser = ArgumentParser(description=__doc__,
                        version="%(prog)s version " + __version__,
                        formatter_class=RawDescriptionHelpFormatter)

parser.add_argument("-H", "--host", 
                    default="localhost:5204",
                    metavar="HOST[:PORT]",
                    help="name or IP address of host (default is 'localhost') "
                    "optionally followed by a port number "
                    "(default is 5204)")

parser.add_argument('-l', '--log', 
                    action='store_true', 
                    help="log requests")

parser.add_argument("-m", "--max-depth", 
                    type=int)

parser.add_argument('-s', '--similarity', 
                    action='store_true', 
                    help="extend interface with word similarity measures "
                    "(requires cdb_lu file with counts)")

parser.add_argument('-V', '--verbose', 
                    action='store_true', 
                    help="verbose output")

parser.add_argument("cdb_lu", 
                    type=file,
                    help="xml file specifying the lexical units")

parser.add_argument("cdb_syn", 
                    type=file,
                    help="xml file specifying the synsets")

args = parser.parse_args()


try:
    host, port = args.host.split(":")[:2]
except ValueError:
    host, port = args.host, None
    
args.host = host or "localhost"


try:
    args.port = int(port or 5204)
except ValueError:
    exit("Error: %s is not a valid port number" % repr(port))
    

start_server(**args.__dict__)    
