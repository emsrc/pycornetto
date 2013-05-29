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
Strips elements, attributes and white space from Cornetto xml database files, 
and writes result to standard output.

The 'default' method strips empty elements and insignificant white space.

In addition, the 'minimal' method strips all elements and attributes which
are not essential for the basic pycornetto interface.
"""

# FEATURES:
# - strip arbitrary elements and attribs to further reduce memory footprint


__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'


from sys import stdout
from cornetto.argparse import ArgumentParser, RawDescriptionHelpFormatter
from xml.etree.cElementTree import iterparse, ElementTree


def strip(inf, strip_method):
    parser = iterparse(inf, events=("start", "end"))
    path = []
    
    for event, elem in parser:
        if event == "start":
            path.append(elem)
        else:
            path.pop()
            
            try:
                strip_method(elem, path[-1])
            except IndexError:
                # parent becomes None because this is the root elem
                strip_method(elem, None)
            
    et = ElementTree(parser.root)
    et.write(stdout, "UTF-8")    
    
    
    
def strip_elem_default(elem, parent):
    # strip trailing whitespace 
    elem.tail = None
    
    try:
        # clear spans containing only whitespace
        if not elem.text.strip():
            elem.text = None
    except AttributeError:
        pass
        
    # remove empty element which
    # has no children AND 
    # has no text AND
    # has no attributes or only empty attributes
    if ( not elem.getchildren() and 
         not elem.text and
         not any(elem.attrib.values()) ):
        remove_elem(elem, parent)
        
        
def strip_elem_minimal(elem, parent):
    # strip whole elements
    if elem.tag not in ( "cdb_lu", "form",
                         "cdb_synset", "synonyms", "synonym",
                         "wn_internal_relations", "relation"):
        remove_elem(elem, parent)
    else:
        strip_elem_default(elem, parent)
    
    # strip attributes
    for attr in elem.attrib.keys():
        if attr not in ("c_lu_id", "c_seq_nr", "form-cat", "form-spelling",
                        "c_sy_id", "d_synset_id",  "target", "relation_name"):
            del elem.attrib[attr] 
            
            
def remove_elem(elem, parent):
    try:
        parent.remove(elem)
    except AttributeError:
        # parent is None because this is the root elem,
        # which cannot be removed
        pass
    
    
    

strip_methods = dict(default = strip_elem_default,
                     minimal = strip_elem_minimal)



parser = ArgumentParser(description=__doc__,
                        version="%(prog)s version " + __version__,
                        formatter_class=RawDescriptionHelpFormatter)

parser.add_argument("file",
                    help="xml file specifying lexical units or synsets")

parser.add_argument("--method", "-m",
                    choices = ["default", "minimal"],
                    default="default",
                    help="method of stripping")

args = parser.parse_args()

            
strip(args.file, 
      strip_methods[args.method])

        

    
