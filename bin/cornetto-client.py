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
A simple client to connect to the Cornetto database server.
Reads queries from standard input and writes results to standard output.
"""

# BUGS:
# - there is no way interrupt a query that goes bad on the server, as obviously
#   a local Ctrl-C does not work


__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'

# using optparse instead of argparse so client can run stand-alone 
from sys import stdin, stdout, stderr, exit
from optparse import OptionParser, IndentedHelpFormatter
import xmlrpclib 
from pprint import pformat
from socket import error as SocketError



class MyFormatter(IndentedHelpFormatter):
    """to prevent optparse from messing up the epilog text"""
    
    def format_epilog(self, epilog):
        return epilog or ""
    
    def format_description(self, description):
        return description.lstrip()
    

epilog = """
Interactive usage:

  $ cornetto-client.py
  $ cornetto-client.py -a
  
File processing:

  $ echo 'ask("pijp")' | cornetto-client.py
  $ cornetto-client.py <input >output
"""

try:
    parser = OptionParser(description=__doc__, version="%(prog)s version " +
                          __version__, epilog=epilog, formatter=MyFormatter())
except TypeError:
    # optparse in python 2.4 has no epilog keyword
    parser = OptionParser(description=__doc__ + epilog, 
                          version="%(prog)s version " + __version__)
    
    


parser.add_option("-a", "--ask", action='store_true',
                  help="assume all commands are input the 'ask' function, "
                  "- so you can type 'query' instead of 'ask(\"query\") -  '"
                  "but online help is no longer accessible" )

parser.add_option("-H", "--host", default="localhost:5204",
                    metavar="HOST[:PORT]",
                    help="name or IP address of host (default is 'localhost') "
                    "optionally followed by a port number "
                    "(default is 5204)")

parser.add_option('-n', '--no-pretty-print', dest="pretty_print", action='store_false', 
                  help="turn off pretty printing of output "
                  "(default when standard input is a file)")

parser.add_option("-p", "--port", type=int, default=5204,
                  help='port number (default is 5204)')

parser.add_option('-P', '--pretty-print', dest="pretty_print", action='store_true', 
                  help="turn on pretty printing of output "
                  "(default when standard input is a tty)")


parser.add_option("-e", "--encoding", default="utf8", metavar="utf8,latin1,ascii,...",
                  help="character encoding of output (default is utf8)")

parser.add_option('-V', '--verbose', action='store_true', 
                  help="verbose output for debugging")


(opts, args) = parser.parse_args()


if opts.host.startswith("http://"):
    opts.host = opts.host[7:]

try:
    host, port = opts.host.split(":")[:2]
except ValueError:
    host, port = opts.host, None
    
# XMP-RPC requires specification of protocol
host = "http://" + (host or "localhost")

try:
    port = int(port or 5204)
except ValueError:
    exit("Error: %s is not a valid port number" % repr(port))

server = xmlrpclib.ServerProxy("%s:%s" %  (host, port),
                               encoding="utf-8",
                               verbose=opts.verbose)
try:
    eval('server.echo("test")')
except SocketError, inst:
    print >>stderr, "Error: %s\nCornetto server not running on %s:%s ?" % (
        inst, host, port), "See cornetto-server.py -h"
    exit(1)

    
help_text = """
Type "?" to see his message.
Type "help()" for help on available methods.
Type "Ctrl-D" to exit.
Restart with "cornetto-client.py -h" to see command line options.
"""

startup_msg = ( "cornetto-client.py (version %s)\n" % __version__ + 
                "Copyright (c) Erwin Marsi\n" + help_text )

    

if stdin.isatty():
    prompt = "$ "
    if opts.pretty_print is None:
        opts.pretty_print = True
    print startup_msg
else:
    prompt = ""
    if opts.pretty_print is None:
        opts.pretty_print = False
    
# use of eval might allow arbitrary code execution - probably not entirely safe    
if opts.ask:
    process = lambda c: eval('server.ask("%s")' % c.strip())
else:
    process = lambda c: eval("server." + c.strip())

if opts.pretty_print:
    formatter = pformat
else:
    formatter = repr

# This is nasty way to enforce encoleast_common_subsumers("fiets", "auto")ding of strings embedded in lists or dicts.
# For examample [u'plafonnière'] rather than [u"plafonni\xe8re"]
encoder = lambda s: s.decode("unicode_escape").encode(opts.encoding, "backslashreplace") 


while True:
    try:
        command = raw_input(prompt)
        if command == "?":
            print help_text
        else:
            result = process(command)
            print encoder(formatter(result))
    except EOFError:
        print "\nSee you later alligator!"
        exit(0)
    except KeyboardInterrupt:
        print >>stderr, "\nInterrupted. Latest command may still run on the server though..."
    except SyntaxError:
        print >>stderr, "Error: invalid syntax"
    except NameError, inst:
        print >>stderr, "Error:", inst, "- use quotes?"
    except xmlrpclib.Error, inst:
        print >>stderr, inst
    except SocketError:
        print >>stderr, "Error: %s\nCornetto server not running on %s:%s ?\n" % (
            inst, host, port), "See cornetto-server.py -h"

