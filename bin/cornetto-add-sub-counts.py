#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
add subsumed word counts to Cornetto lexical units database file

The "subsumed word count" is the count of a word itself plus the counts of all
words that it subsumes (in terms of the hyperonym/hyponym relation). It
assumed that every <form> element has a "count" attribute, as a result from
running cornetto-add-counts.py first. The subsumed word counts appear as the
value of the feature "subcount" on <form> elements. The updated lexical units
xml database is written to standard output. 
"""

__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'

from distutils.version import LooseVersion
import networkx

if LooseVersion(networkx.__version__) < LooseVersion('1.0'):
    raise ImportError("pycornetto requires networkx version 1.0rc1 or later" +
                      "(this is version {0!r}".format(networkx.__version__))

from sys import stderr, stdout
from xml.etree.cElementTree import ElementTree, iterparse, tostring

from cornetto.argparse import ArgumentParser, RawDescriptionHelpFormatter
from cornetto.cornet import Cornet
from cornetto.parse import _parse_cdb_syn, _relations_to_edges, _parse_lex_units

# General remark:
# This is probably not the most effcient way to accomplish this task,
# but it is a one-time operation only...

    
def tweaked_parse_cdb(cdb_lu, cdb_syn, verbose=False):
    """
    tweaked version of parser.parse_cdb which also returns the element tree
    for the lexical units
    """
    graph = networkx.MultiDiGraph()

    form2lu, c_lu_id2lu, lu_etree = tweaked_parse_cdb_lu(cdb_lu, graph,
                                                         verbose=verbose)

    sy_id2synset, sy_id2lus = _parse_cdb_syn(cdb_syn, c_lu_id2lu,
                                             verbose=verbose)

    _relations_to_edges(c_lu_id2lu, sy_id2synset, sy_id2lus, graph,
                        verbose=verbose)
    
    # drop sy_id2lus
    return form2lu, c_lu_id2lu, sy_id2synset, graph, lu_etree 



def tweaked_parse_cdb_lu(file, graph, verbose=False):
    """
    tweaked version of parser._parse_cdb_lu which also returns the element tree
    for the lexical units
    """
    parser = iterparse(file)
    form2lu, c_lu_id2lu = _parse_lex_units(parser, graph, verbose) 
    lu_etree = ElementTree(parser.root)
    return form2lu, c_lu_id2lu, lu_etree




class TweakedCornet(Cornet):
        
    def open(self, cdb_lu, cdb_syn, verbose=False):
        """
        also stores element tree for lexical units in self._lu_etree
        """
        ( self._form2lu, 
          self._c_lu_id2lu,
          self._c_sy_id2synset, 
          self._graph,
          self._lu_etree ) = tweaked_parse_cdb(cdb_lu, cdb_syn, verbose)
    
        
        
    def write_cdb_lu(self, out=stdout):
        # tricky: remove the added attribute "c_sy_id" which points to the
        # synsets a lu belongs to, otherwise it will be doubled when the file
        # is read again!
        for lu in self._lu_etree.findall("//cdb_lu"):
            try:
                del lu.attrib["c_sy_id"]
            except KeyError:
                pass
            
        out.write('<?xml version="1.0" encoding="utf-8"?>\n')    
        self._lu_etree.write(out, encoding="utf-8")
        
        
    def add_sub_counts(self):
        # Problem: no senses
        #
        # Since we have only the lemma and the POS, and no word sense, the word counts
        # are added to each lexical unit with matching form-spelling and form-cat,
        # regardless of its sense (i.e. the value of the "c_seq_nr" attribute).
        # So for example xxx:noun:1 and xxx:noun:2 receive the same count value, 
        # i.e. count( xxx:noun:1) = n and count(xxx:noun:2) = n.
        # Now suppose yyyy:noun:1 is a subsumer of both xxx:noun:1 and xxx:noun:2,
        # which happens quite frequently, then its subcount is incremented by n twice!
        # This is not what we want, because it means the contribution of words with 
        # multiple senses is overestimated.
        #
        # Solution:
        # We keep a track of lexical units already vistited while processing this word form.
        # That is, upon visiting yyyy:noun:1 as a subsumer of xxx:noun:2, it is skipped.
        #
        # Note:
        # The problem does not occur across categories (verified). That is, it never happens
        # that xxx:noun and xxx:verb share a common subsumer. This simplifies matters and
        # saves us some administration.
        for lus in self._form2lu.values():
            visited = dict.fromkeys(lus)
            
            for lu in lus:
                form = lu.find("form")
                
                try:
                    count = int(form.get("count"))
                except (AttributeError, TypeError):
                    # form or count not found
                    stderr.write("Warning: no <form> element or 'count' attribute in:\n" +
                                 tostring(lu).encode("utf-8") + "\n")
                    continue
                
                if not form.get("subcount"):
                    # init subcount to count itself, unless it was already visited as a subsumer
                    form.set("subcount", str(count))
                
                # FIXME: reimplementing this without the overhead of keeping
                # track of the distance would be faster
                successors = self._transitive_closure([lu], "HAS_HYPERONYM").keys()
                
                for succ_lu in successors:
                    if succ_lu not in visited:
                        succ_lu_form = succ_lu.find("form")
                        
                        try:
                            succ_count = succ_lu_form.get("count")
                            old_subcount = int(succ_lu_form.get("subcount", succ_count))
                        except (TypeError, AttributeError):
                            # form or count not found
                            stderr.write("Warning: no <form> element or 'count' attribute in:\n" +
                                         tostring(succ_lu).encode("utf-8") + "\n")
                            continue
                            
                        new_subcount = old_subcount + count
                        succ_lu_form.set("subcount", str(new_subcount))


                        
parser = ArgumentParser(description=__doc__,
                        version="%(prog)s version " + __version__,
                        formatter_class=RawDescriptionHelpFormatter)

parser.add_argument("cdb_lu", type=file,
                    help="xml file specifying the lexical units")

parser.add_argument("cdb_syn", type=file,
                    help="xml file specifying the synsets")

args = parser.parse_args()



c = TweakedCornet(args.cdb_lu, args.cdb_syn)
c.add_sub_counts()
c.write_cdb_lu()

    


