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
parse the xml files which define the Cornetto database
"""

# TODO:
# - remove code which cirumvents cdb bugs

__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'


from sys import stderr
from xml.etree.cElementTree import ElementTree, Element, iterparse, tostring

from distutils.version import LooseVersion
import networkx

if LooseVersion(networkx.__version__) < LooseVersion('1.0'):
    raise ImportError("pycornetto requires networkx version 1.0rc1 or later" +
                      "(this is version {0!r}".format(networkx.__version__))



def _parse_cdb_lu(file, graph, verbose=False):
    """
    Parse xml file which defines the lexical units.
    Add lexical units (as Element) to the XiGraph graph.
    Return the mappings form-->lexical units and
    lexical-unit-id-->lexical-unit
    """
    parser = iterparse(file)
    return _parse_lex_units(parser, graph, verbose)



def _parse_lex_units(parser, graph, verbose=False):
    form2lu = {}
    c_lu_id2lu = {}
    
    for event, elem in parser:
        if elem.tag == "cdb_lu":
            # make sure this attrib is NOT already present,
            # because we are going to add it in _synonym_relations_to_edges()
            assert not elem.get("c_sy_id")
            
            c_lu_id = elem.get("c_lu_id")
            # REMOVE-ME: check unique id
            assert c_lu_id and c_lu_id not in c_lu_id2lu
            
            graph.add_node(elem)
            c_lu_id2lu[c_lu_id] = elem
            
            # note that value can be ascii or unicode (peculiarity of ElementTree)
            form = form_elem.get("form-spelling")
            
            # REMOVE-ME: form should never be None 
            if form:
                form2lu.setdefault(form, []).append(elem)
            elif verbose:
                print >>stderr, ("Warning: form element in lexical unit with id "
                                 + repr(c_lu_id) + " has no 'form-spelling' attribute")
                continue
            
            # fix category flaws (ADJECTIVE, ADVERB, NOUN, VERB) in current
            # release of Cornetto
            cat = form_elem.get("form-cat", "")
            newcat = cat.lower()

            if newcat == "adjective":
                newcat = "adj"
            elif newcat == "adverb":
                newcat = "adv"
                
            if newcat != cat:
                if verbose:
                    form_elem.set("form-cat", newcat)
                    print >>stderr, ("Warning: changed cat from " + repr(cat)
                                     + " to " + repr(newcat) + " in lexical unit with id " +
                                     repr(c_lu_id))
            
        elif elem.tag == "form":
            form_elem = elem
            
            
    return form2lu, c_lu_id2lu



def _parse_cdb_syn(file, c_lu_id2lu, verbose=False):
    """
    Parse xml file which defines the synsets.
    Return the mappings synset-id-->synset and
    synset-id-->list-of-lexical-units
    """
    # FIXME
    # It seems that the "target" attrib in the <relation> element,
    # which specifies wn_internal relations,
    # is using both cornetto id's (the "c_sy_id" attrib on <cdb_synset>) or 
    # word id's (the "d_synset_id" on <cdb_synset>) to identify
    # related synsets. Hence, the sy_id2synset table stores both.
    # The downside is tha he table becomes larger.
    # This will probably be fixed in future releases of Cornetto.
    sy_id2synset = {}

    # This is a trading off space against speed,
    # because otherwise we have to parse the <synonsyms> sections multiple times.
    # This table will dropped once parse_cdb is finished.
    sy_id2lus = {}
    lus = []
    # REMOVE-ME: a list a synonym lu id's, because cdb is still buggy and
    # sometimes targets the same lu multiple times
    seen_lu_ids = []
    
    parser = iterparse(file)
    
    for event, elem in parser:
        if elem.tag == "cdb_synset":
            c_sy_id = elem.get("c_sy_id")

            if c_sy_id and c_sy_id not in sy_id2synset:
                sy_id2synset[c_sy_id] = elem
                # a superficial copy of the list of lexical units
                sy_id2lus[c_sy_id] = lus[:]
            
            d_synset_id = elem.get("d_synset_id")
            # not always present and may be identical to c_cy_id
            if d_synset_id and d_synset_id != c_sy_id:
                sy_id2synset[d_synset_id] = elem
                # reuse the same copy of lus
                sy_id2lus[d_synset_id] = sy_id2lus[c_sy_id] 
                
            lus = []
            seen_lu_ids = []
        elif elem.tag == "synonym":
            c_lu_id = elem.get("c_lu_id")
            
            try:
                lu = c_lu_id2lu[c_lu_id]
            except KeyError:
                if verbose: print >>stderr, ( "Warning: lu with id " +
                                              repr(c_lu_id) + " does not exist" )
                continue
            
            if c_lu_id not in seen_lu_ids:
                lus.append(lu)
                seen_lu_ids.append(c_lu_id)
            
    return sy_id2synset, sy_id2lus


def _relations_to_edges(c_lu_id2lu, sy_id2synset, sy_id2lus, graph, verbose=False):
    """
    Convert relations to graph edges 
    """
    # FIXME
    # A synset may appear twice in the table sy_id2synset 
    # so  we cannot iterate over its values directly.
    # Instead, we must determine unqiue values first.
    # (see remark for parse_cdb_syn)
    for synset_el in set(sy_id2synset.values()):                    
        _synonym_relations_to_edges(synset_el, c_lu_id2lu, sy_id2lus, graph, verbose=False)
        _wn_internal_relations_to_edges(synset_el, c_lu_id2lu, sy_id2lus,
                                        graph, verbose=verbose)
        
        
def _synonym_relations_to_edges(synset_el, c_lu_id2lu, sy_id2lus, graph,
                                verbose=False):
    """
    Add edges between all synonym lexical units in the graph.
    Also add a new 'c_sy_id' attribute to lexical unit elements 
    which lists all synsets this unit belongs to.
    """
    c_sy_id = synset_el.get("c_sy_id")
    nodes = sy_id2lus[c_sy_id]
    
    for from_node in nodes:
        # For later reference, add a pointer to all synset id's to which this
        # lu belongs. Yes, a lexical unit can belong to multiple synsets.
        try:
            from_node.set("c_sy_id", from_node.get("c_sy_id") + "," + c_sy_id)
        except TypeError:
            from_node.set("c_sy_id", c_sy_id)
        
        for to_node in nodes:
            if from_node is not to_node:
                add_edge(graph, from_node, to_node, relation="SYNONYM",
                         verbose=verbose)
                
                
def add_edge(graph, from_node, to_node, relation, verbose=False):
    # this filters out some obviously wrong relations still present in
    # Cornetto
    
    # 1. prevent self-refering relations
    if from_node == to_node:
        if verbose:
            lu_id = from_node.get("c_lu_id")
            print >>stderr, ( "Warning: filtered self-referring relation " +
                              repr(relation) + " on lexical unit " + repr(lu_id) )
        return
    
    # 2. prevent multi-edges with identical relations
    try:
        for attr in graph[from_node][to_node].values():
            if attr["relation"] == relation:
                if verbose:
                    from_lu_id = from_node.get("c_lu_id")
                    to_lu_id = to_node.get("c_lu_id")
                    print >>stderr, ( "Warning: filtered duplicate relation "
                                      + repr(relation) + " between lexical unit " +
                                      repr(from_lu_id) + " and " + repr(to_lu_id) )
                return
    except KeyError:
        # no edge yet
        pass
    
    graph.add_edge(from_node, to_node, relation=relation)

    
def _wn_internal_relations_to_edges(synset_el, c_lu_id2lu, sy_id2lus, graph,
                                    verbose=False):
    """ 
    Add edges between lexical units from this synset to other lexical units
    from related synsets.
    """
    c_sy_id = synset_el.get("c_sy_id")
    from_nodes = sy_id2lus[c_sy_id]
        
    for relation_el in synset_el.find("wn_internal_relations") or []:
        relation = relation_el.get("relation_name")
        # target can identify another synset by c_sy_id or d_synset_id
        target = relation_el.get("target")
        
        try:
            to_nodes = sy_id2lus[target]
        except KeyError:
            # FIXME: this may report the same error many times
            if verbose: print >>stderr, ( "Warning: synset with id " +
                                          repr(target) + " does not exist" )
            continue
        
        for from_node in from_nodes:
            for to_node in to_nodes:
                # here we are losing all other info on <relation>
                # apart from the attrib relation_name...
                add_edge(graph, from_node, to_node, relation=relation,
                         verbose=verbose)

                
                
def parse_cdb(cdb_lu, cdb_syn, verbose=False):
    """
    parse the xml files which define the Cornetto database
    
    Returns a tuple with the following information:
    
        1. form2lu: a dict mapping word forms (i.e. a value of the 
                    "form-spelling" attribute on a <form> element) to  the
                    corresponding lexical unit (i.e. an Element instance 
                    resulting from parsing the <cdb_lu> xml string)
    
        2. c_lu_id2lu: a dict which maps cornette lexical unit identifiers
                       (i.e. the value of the c_lu_id attribute on a <cdb_lu>
                       element) to a lexical unit (i.e. an Element instance
                       resulting from parsing the <cdb_lu> xml string)
                       
        3. sy_id2synset: a dict which maps cornette/wordnet synset identifiers
                       (i.e. the value of the "c_sy_id" or "d_synset_id" attribute 
                       on a <cdb_synset> element) to a lexical unit (i.e. an Element 
                       instance resulting from parsing the <cdb_synset> xml string)
                       
        4. graph: an instance of a subclass of Graph from the networkx package, where 
                  - nodes are Element instances corresponding <cdb_lu> xml strings
                  - edges are Element instances corresponding to <relation> elements
                    or to the synonym relation which holds between members of the 
                    same synset
           The graph will XDiGraph for Networkx versions <= 0.37 and MultiDiGraph
           for networkx versions >= 0.99
    
    @param cdb_lu: xml definition of the lexical units
    @type cdb_lu: file or filename
    
    @param cdb_syn: xml definition of the synsets
    @type cdb_syn: file or filename

    @keyword verbose: verbose output during parsing
    @type verbose: bool
    
    @return: tuple(dict, dict, dict, Graph subclass)
    """
    graph = networkx.MultiDiGraph()

    form2lu, c_lu_id2lu = _parse_cdb_lu(cdb_lu, graph, verbose=verbose)

    sy_id2synset, sy_id2lus = _parse_cdb_syn(cdb_syn, c_lu_id2lu,
                                             verbose=verbose)

    _relations_to_edges(c_lu_id2lu, sy_id2synset, sy_id2lus, graph,
                        verbose=verbose)
    
    # drop sy_id2lus
    return form2lu, c_lu_id2lu, sy_id2synset, graph 


#-------------------------------------------------------------------------------
# parse cdb_lu file with counts
#-------------------------------------------------------------------------------

def _parse_count_totals(parser):
    """
    parse per category and overall counts 
    from attributes of cdb_lu document root
    """
    cat2count = dict()
    
    for cat in "noun verb adj other all".split(): 
        try:
            cat2count[cat] = int(parser.root.get("count-total-%s" % cat))
        except TypeError:
            print >>stderr, "ERROR: This cdb_lu file seems to have no counts!" 
            raise
        
    return cat2count


def _parse_cdb_lu_with_counts(file, graph, verbose=False):
    """
    an extension of _parse_cdb_lu which also parses the count totals
    """
    parser = iterparse(file)
    form2lu, c_lu_id2lu = _parse_lex_units(parser, graph, verbose)
    cat2counts = _parse_count_totals(parser)
    _check_subcounts(parser)
    return form2lu, c_lu_id2lu, cat2counts


def _check_subcounts(parser):
    """
    check that (at least one of the) lexical units have a 'subcounts'
    attribute
    """
    for form_el in parser.root.getiterator("form"):
        if form_el.get("subcount"):
            return
        
    print >>stderr, "ERROR: This cdb_lu file seems to have no subcounts!" 
    raise TypeError


def parse_cdb_with_counts(cdb_lu, cdb_syn, verbose=False):
    """
    an extension of parse_cdb which also parses the count totals
    """
    graph = networkx.MultiDiGraph()

    form2lu, c_lu_id2lu, cat2counts = \
    _parse_cdb_lu_with_counts(cdb_lu, graph, verbose=verbose)

    sy_id2synset, sy_id2lus = \
    _parse_cdb_syn(cdb_syn, c_lu_id2lu, verbose=verbose)

    _relations_to_edges(c_lu_id2lu, sy_id2synset, sy_id2lus, graph,
                        verbose=verbose)
    
    # drop sy_id2lus
    return form2lu, c_lu_id2lu, sy_id2synset, graph, cat2counts






