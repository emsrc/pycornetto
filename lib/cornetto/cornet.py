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
the Cornet class which exposes the Cornetto xml database
"""

# BUGS/ISSUES:
# - inst.ask("slang +") takes forever (if no depth limit is set);
#   perhaps change search from recursive DFS to deqeue based BFS?

# TODO:
# - deal with multi word units
# - write unit tests
# - remove code to circumvent bugs in the cornetto db
# - more code comments

# FEATURES:
# - optmization: for testing hypernym and meronym relation, 
#   a unidirectional BFS starting from the most specific/smallest part 
#   is probably faster than the current bidirectional BFS
# - option to supply xpath querys on xml
# - pprinted xml



__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'


from collections import deque
from cornetto.parse import parse_cdb
from xml.etree.cElementTree import tostring


class Cornet(object):    
    """
    The Cornet class exposes the Cornetto xml database
    
    Most public methods require input in the form of a shorthand for
    specifying lexical units and relations, as described below.
    
    
    B{Lexical units specifications}
    
    A specification of lexical units consists of three parts, separated by a
    single colon (':') character:
    
        1. Spelling form (i.e. a word)
        
           This can be any string without white space
           
        2. Syntactic category (optional)
        
           This can be any of 'noun', 'verb' or 'adj'.
           
        3. A sense (optional)
        
           This is number which distinguishes the particular word sense
       
    Examples of valid lexical unit specifications are:
    
       - slang:noun:1
       - slang:noun
       - slang::1
       - slang
    
    
    B{Relation specifications}
    
    A specification of a relation consists of two parts:
    
        1. Relation name (optional)
        
           The name of a Wordnet relation between two synsets. See the
           Cornetto documentation for the available relations. If not given,
           all relations are tried. The special relation "SYNONYM" holds
           between all members of the same synset. The relation name is not
           case-sensitive; you can use lower case.
        
        2. Depth (optional)
        
           A digit ('0' to '9') or the plus sign ('+'). This represents the
           depth of the relations that are considered during search. In other
           words, the maximal number of links allowed. If not given a default
           value of 1 is used. The plus represents the system maximum
           (currently 9).
           
    A relation specification must have a name, a depth or both. Valid
    relation specification include:
        
        - HAS_HYPERONYM
        - HAS_HYPERONYM1
        - HAS_HYPERONYM+
        - 3
        - +
    """

    # ------------------------------------------------------------------------------        
    # Public methods
    # ------------------------------------------------------------------------------        

    _unit_separator = ":"
    _handled_output_formats = ("spec", "xml", "raw")
    _default_output_format = "spec"    
    _default_max_depth = 9

    
    def __init__(self, cdb_lu=None, cdb_syn=None, 
                 output_format=_default_output_format,
                 max_depth=_default_max_depth):
        """
        Create a new Cornet instance
        
        @keyword cdb_lu: an xml file(name) to read the lexical units from 
        @keyword cdb_syn: an xml file(name) to read the synsets from 
        @keyword default_format: default output format
        @type default_format: string ('spec', 'xml', 'raw')
        @keyword max_depth: a maximal depth between 1 and 9
        @type max_depth: int
        """
        
        if cdb_lu and cdb_syn:
            self.open(cdb_lu, cdb_syn)
            
        self.set_output_format(output_format) 
        self.set_max_depth(max_depth)

            
    def open(self, cdb_lu, cdb_syn, verbose=False):
        """
        Open and parse Cornetto database files
        
        @param cdb_lu: xml definition of the lexical units
        @type cdb_lu: file or filename
        @param cdb_syn: xml definition of the synsets
        @type cdb_syn: file or filename
        @keyword verbose: verbose output during parsing
        """
        ( self._form2lu, 
          self._c_lu_id2lu,
          self._c_sy_id2synset, 
          self._graph ) = parse_cdb(cdb_lu, cdb_syn, verbose)
    
    
    def ask(self, query, format=None):
        """
        Pose a query about lexical units to the Cornetto database
        
        This supports three different types of queries:
        
            1. Getting lexical units
            
               If the query consists of only a lexical unit specification the
               answer lists all lexical units which satisfy this
               specification. See also L{get_lex_units}
            
            2. Getting related lexical units
            
               If the query consists of a lexical unit specification plus a
               relation specification, the answer consists of all lexical
               units related by the specified relation(s). See also
               L{get_related_lex_units}
            
            3. Testing relations between lexical units
            
               If the query consists of a lexical unit specification, plus a
               relation specification plus another lexical specification, the
               answer is a path from the first to the second lexical unit(s)
               along the specified relation(s). See also
               L{test_lex_units_relation}
        
        @param query: a specification
        @type query: string 
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: depends on type of query an output format
        """
        from_spec, rel, to_spec = self._split_query(query)
        
        if to_spec:
            return self.test_lex_units_relation(from_spec, rel, to_spec, format)
        elif rel:
            return self.get_related_lex_units(from_spec, rel, format)
        else:
            return self.get_lex_units(from_spec, format)    
        

    def get_lex_units(self, spec, format=None):
        """
        Get all lexical units which satisfy this specification
        
        
        >>> inst.get_lex_units("lamp")
        ['lamp:noun:3', 'lamp:noun:4', 'lamp:noun:1', 'lamp:noun:2']
        
        >>> inst.get_lex_units("varen")
        ['varen:verb:3', 'varen:noun:1', 'varen:verb:1', 'varen:verb:2']

        >>> inst.get_lex_units("varen:noun")
        ['varen:noun:1']

        >>> inst.get_lex_units("varen:verb:3")
        ['varen:verb:3']

        >>> inst.get_lex_units("varen:noun:3")
        []
        
        
        @param spec: lexical unit specification
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @rtype: list
        @return: list of lexical units in requested output format
        """
        form, cat, sense = self._split_unit_spec(spec)
        formatter = self._get_lex_unit_formatter(format)
        
        return [ formatter(lu) 
                 for lu in self._form2lu.get(form, [])
                 if ( self._lu_has_cat(lu, cat) and 
                      self._lu_has_sense(lu, sense) ) ]
    

    def get_related_lex_units(self, lu_spec, rel_spec, format=None):
        """
        For all specified lexical units,
        find all lexical units related by the specified relation.
          
        The search may be constrained by the setting of the maximum search depth; 
        see set_max_depth.
        
        
        >>> pprint(inst.get_related_lex_units("slang", "SYNONYM"))
        {'slang:noun:1': {'SYNONYM': {'serpent:noun:2': {}}},
         'slang:noun:2': {},
         'slang:noun:3': {'SYNONYM': {'pin:noun:2': {}, 'tang:noun:2': {}}},
         'slang:noun:4': {'SYNONYM': {'groepstaal:noun:1': {},
                                      'jargon:noun:1': {},
                                      'kringtaal:noun:1': {}}},
         'slang:noun:5': {'SYNONYM': {'muntslang:noun:1': {}}},
         'slang:noun:6': {'SYNONYM': {'Slang:noun:1': {}}}}

        >>> pprint(inst.get_related_lex_units("slang::1", "1"))
        {'slang:noun:1': {'HAS_HOLO_MEMBER': {'slangegebroed:noun:1': {},
                                              'slangengebroed:noun:2': {}},
                          'HAS_HYPERONYM': {'reptiel:noun:1': {}},
                          'HAS_HYPONYM': {'cobra:noun:1': {},
                                          'gifslang:noun:1': {},
                                          'hoedslang:noun:1': {},
                                          'hydra:noun:2': {},
                                          'lansslang:noun:1': {},
                                          'lepelslang:noun:1': {},
                                          'python:noun:2': {},
                                          'ratelslang:noun:1': {},
                                          'ringslang:noun:1': {},
                                          'rolslang:noun:1': {},
                                          'waterslang:noun:3': {},
                                          'wurgslang:noun:1': {},
                                          'zeeslang:noun:1': {}},
                          'HAS_MERO_PART': {'slangekop:noun:1': {},
                                            'slangenkop:noun:1': {}},
                          'SYNONYM': {'serpent:noun:2': {}}}}
                          
                                               
        @param lu_spec: lexical unit(s) specification of source
        @param rel_spec: relation(s) specification
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @rtype: dict
        @return: an hierachical dict structure with lexical units and relations as keys 
        """  
        rel_name, depth = self._split_rel_spec(rel_spec)
        
        if not rel_name:
            if rel_spec == "+":
                # silently change to max allowed search depth
                depth = self._max_depth
            elif depth > self._max_depth:
                raise ValueError("requested search depth (%d) is larger than "
                                 "maximum search depth (%d)" % (depth, self._max_depth))
        
        lu_formatter = self._get_lex_unit_formatter(format)
        rel_formatter = self._get_relation_formatter(format)
        related_lus = {}
        
        for from_lu in self.get_lex_units(lu_spec, format="raw"):
            from_lu_repr = lu_formatter(from_lu)
            
            related_lus[from_lu_repr] = \
            self._search_related_lex_units(from_lu, rel_name, depth, 
                                           lu_formatter, rel_formatter, [from_lu])
            
        return related_lus
    
    
    def test_lex_units_relation(self, from_lu_spec, rel_spec, to_lu_spec, format=None):
        """
        Test if certain relation(s) hold between certain lexical units by
        searching for a a path from any of the source lexical units to any of
        target lexical unit(s) along one or more of the specified relation(s)
        
        
        >>> inst.test_lex_units_relation("lamp", "HAS_HYPONYM", "gloeilamp")
        ['lamp:noun:2', 'HAS_HYPONYM', 'gloeilamp:noun:1']
        
        >>> inst.test_lex_units_relation("lamp", "HAS_HYPONYM2", "fotolamp")
        ['lamp:noun:2', 'HAS_HYPONYM', 'gloeilamp:noun:1', 'HAS_HYPONYM', 'fotolamp:noun:1']
        
        >>> inst.test_lex_units_relation("lamp", "HAS_HYPONYM", "fotolamp")
        []
        
        
        @param from_lu_spec: lexical unit specification of the source(s)
        @param rel_spec: relation(s) specification
        @param to_lu_spec: lexical unit specification of the target(s)
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: list of lexical units and relations in requested output format,
                 possibly empty
        @rtype: list 
        
        @warning: The result may not be the only shortest path.
        """
        rel_name, depth = self._split_rel_spec(rel_spec)
        
        from_lus = self.get_lex_units(from_lu_spec, format="raw")
        to_lus = self.get_lex_units(to_lu_spec, format="raw")
        
        pred, common_lu, succ = self._bidirectional_shortest_path(from_lus, to_lus, rel_name, depth) 
        path = self._reconstruct_path(pred, common_lu, succ, format)
        return path
        
                 
        
    def get_synsets(self, spec, format=None):
        """
        Get all synsets containing lexical units which satisfy a certain
        specification.
        
        
        >>> pprint(inst.get_synsets("slang"))
        [['Slang:noun:1', 'slang:noun:6'],
         ['slang:noun:5', 'muntslang:noun:1'],
         ['slang:noun:1', 'serpent:noun:2'],
         ['slang:noun:2'],
         ['tang:noun:2', 'pin:noun:2', 'slang:noun:3'],
         ['jargon:noun:1', 'groepstaal:noun:1', 'kringtaal:noun:1', 'slang:noun:4']]
         
         >>> pprint(inst.get_synsets("slang:noun:5"))
         [['slang:noun:5', 'muntslang:noun:1']]

         >>> pprint(inst.get_synsets("slang:noun:7"))
         []
        
         
        @param spec: lexical unit specification 
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: list of synsets (lists) with lexical units in requested 
                 output format 
        @rtype: list
         
        """
        form, cat, sense = self._split_unit_spec(spec)
        synsets = []
        formatter = self._get_synset_formatter(format)
        
        for lu in self._form2lu.get(form, []):
            if ( self._lu_has_cat(lu, cat) and 
                 self._lu_has_sense(lu, sense) ): 
                # Using new attribute added while parsing synonym relations
                # to find the id's of all synsets to which this lu belongs.
                # Alternatively, we could use the graph to find all lu's which
                # are synonym to this lu.
                for c_sy_id in lu.get("c_sy_id", "").split(","):
                    try:
                        sy = self._c_sy_id2synset[c_sy_id]
                    except KeyError:
                        # oops, there is no synset with this id
                        continue
                    synsets.append(formatter(sy))
                
        return synsets

        
    def get_related_synsets(self, lu_spec, rel_name=None, format=None):
        # Not very useful. Remove this method?
        # Or generalize to relation spec?
        """
        For all synsets containing lexical units satisfying this specification
        find the related synsets along this relation.  
        If no relation is given, all relations are considered.
        

        >>> pprint(inst.get_related_synsets("lamp", "HAS_HYPERONYM"))
        {'HAS_HYPERONYM': [['armatuur:noun:1', 'verlichtingsarmatuur:noun:1'],
                           ['lamp:noun:2', 'licht:noun:13', 'lichtje:noun:1'],
                           ['lichtbron:noun:1'],
                           ['voorwerp:noun:1', 'ding:noun:1']]}
        
        >>> pprint(inst.get_related_synsets("slang::1"))
        {'HAS_HOLO_MEMBER': [['slangegebroed:noun:1', 'slangengebroed:noun:2']],
         'HAS_HYPERONYM': [['reptiel:noun:1']],
         'HAS_MERO_PART': [['slangekop:noun:1', 'slangenkop:noun:1']]}
         

        @param lu_spec: lexical unit(s) specification of source
        @param rel_name: relation name
        
        @return: a dict with relations as keys and lists of synsets as values
        @rtype: dict
        
        @note: Parameter rel_name is a relation name, not a relation specification.
               Search is thus not transitive.
        """
        form, cat, sense = self._split_unit_spec(lu_spec)
        if rel_name: rel_name = rel_name.upper()
        syn_formatter = self._get_synset_formatter(format)
        rel_formatter = self._get_relation_formatter(format)
        related_syns = {}
        
        # lazy and slow
        for from_syn in self.get_synsets(lu_spec, format="raw"):
            for rel in from_syn.find("wn_internal_relations") or []:
                if self._rel_has_name(rel, rel_name):
                    to_syn_id = rel.get("target")
                    to_syn = self._c_sy_id2synset[to_syn_id]
                    
                    syn_repr = syn_formatter(to_syn)
                    rel_repr = rel_formatter(rel)

                    related_syns.setdefault(rel_repr, []).append(syn_repr)
                        
        return related_syns
    

    def get_lex_unit_by_id(self, c_lu_id, format=None):
        """
        Get lexical unit by id
        
        @param c_lu_id: Tvalue of the C{c_lu_id} attribute at C{<cdb_lu>} element
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @rtype: string or None 
        @return: lexical unit in the requested output format or None 
        """
        formatter = self._get_lex_unit_formatter(format)
        
        try:
            return formatter(self._c_lu_id2lu[c_lu_id])
        except KeyError:
            return None
        
        
    def get_synset_by_id(self, c_sy_id, format=None):
        """
        Get synset by id
        
        @param c_sy_id: value of the C{c_sy_id} attribute at C{<cdb_synset>} element
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: set (list) of lexical units in the requested output format
        @rtype: list or None
        """
        formatter = self._get_synset_formatter(format)
        
        try:
            return formatter(self._c_sy_id2synset[c_sy_id])
        except KeyError:
            return None

    def get_lex_unit_from_synset(self, c_sy_id, lemma, format=None): #added by Maarten van Gompel
        """Get a lexical unit based on a synset ID and a lemma"""
        try:
            synset = self._c_sy_id2synset[c_sy_id]
        except KeyError:
            return None

        
        formatter = self._get_lex_unit_formatter(format)

        c_lu_id = None

        for syn in synset.find("synonyms") or []:
            c_lu_id = syn.get("c_lu_id")
            try:
                lu = self._c_lu_id2lu[c_lu_id]
                luform = self._get_lu_form(lu) #get form-spelling (lemma)
                if luform == lemma:
                    #this one matches with the lemma we specified, return it!
                    return formatter(lu)
            except KeyError:
                # no lu with this id
                continue

        return None #nothing found



        
        
    def all_common_subsumers(self, lu_spec1, lu_spec2,
                             rel_name="HAS_HYPERONYM", format=None):
        """
        Finds all common subsumers of two lexical units over the given
        relation. The common subsumers are grouped according to the lenght of
        the path (in edges) from the first lexical unit to the subsumer to the
        second lexical unit.

        
        >>> pprint(c.all_common_subsumers("kat", "hond"))
        {2: ['huisdier:noun:1', 'zoogdier:noun:1'],
         4: ['beest:noun:2', 'gedierte:noun:2', 'dier:noun:1'],
         5: ['ziel:noun:3',
             'homo sapiens:noun:1',
             'sterveling:noun:1',
             'mens:noun:1',
             'mensenkind:noun:1'],
         6: ['organisme:noun:2'],
         8: ['wezen:noun:1', 'schepsel:noun:1', 'creatuur:noun:2'],
         9: ['iets:noun:2'],
         10: ['object:noun:3']}

        
        @param lu_spec1: first lexical unit(s) specification
        @param rel_name: relation name (not a specification)
        @param lu_spec2: second lexical unit(s) specification
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: a dict with path lenghts as key and lists of common subsumers
                 as values, possibly empty
        @rtype: dict
        
        @note: this method will only make sense for some relations
               (typically HAS_HYPERONYM) but not for others
               (e.g. SYNONYM)
        """
        rel_name = rel_name.upper()
        formatter = self._get_lex_unit_formatter(format)
        
        lus1 = self.get_lex_units(lu_spec1, format="raw")
        sucs1 = self._transitive_closure(lus1, rel_name)
        
        # Add lus themselves as succesors with zero distance
        # This acounts for cases where lu1 equals lu2 or
        # where one lu is a hyperonym of the other lu.
        for lu in lus1:
            sucs1[lu] = 0
        
        lus2 = self.get_lex_units(lu_spec2, format="raw")
        sucs2 = self._transitive_closure(lus2, rel_name)
        
        # idem for lus2
        for lu in lus2:
            sucs2[lu] = 0

        acs = dict()

        for lu, dist in sucs1.items():
            try:
                sum_of_dist = dist + sucs2[lu]
            except KeyError:
                continue
            
            acs.setdefault(sum_of_dist, []).append(formatter(lu))
            
        return acs
    
    
    def least_common_subsumers(self, lu_spec1, lu_spec2, 
                               rel_name="HAS_HYPERONYM", format=None):
        """
        Finds the least common subsumers of two lexical units over the given
        relation, that is, those common subsumers of which the lenght of
        the path (in edges) from the first lexical unit to the subsumer to the
        second lexical unit is minimal.
        
        
        >>> c.least_common_subsumers("kat", "hond")
        ['huisdier:noun:1', 'zoogdier:noun:1']

        
        @param lu_spec1: first lexical unit(s) specification
        @param rel_name: relation name (not a specification)
        @param lu_spec2: second lexical unit(s) specification
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: a lists of the least common subsumers, possibly empty
        @rtype: list
        
        @note: this method will only make sense for some relations
               (typically HAS_HYPERONYM) but not for others
               (e.g. SYNONYM)
        """
        # It might not be neccessary to compute all common subsumers, i.e. the 
        # transtive closure of both lu's, before we can decide for sure
        # which sum of distances is the minimal one, but it is not easy to avoid.
        # The reason is that one large distance of an lcs to lu1 may be compensated 
        # for by a small or zero distance to lu2. 
        # TODO: this point needs more explanation 
        acs = self.all_common_subsumers(lu_spec1, lu_spec2, rel_name, format)
        
        if acs:
            minimum = min(acs.keys())
            return acs[minimum]
        else:
            return []
        
        
    def set_output_format(self, format=_default_output_format):
        """
        Change the default output format
        
        @param format: output format
        @type format: 'spec', 'xml', 'raw'
        """
        if format in self._handled_output_formats:
            self._output_format = format
        else:
            raise ValueError("unknown output format: " + format + " not in " +
                             self._handled_output_formats)   
        
        
    def set_max_depth(self, max_depth=_default_max_depth):
        """
        Sets a limit on the maximal depth of searches for related lexical units 
        where no relation name is specified.
        
        @param max_depth: a maximal depth between 1 and 9
        @type max_depth: int
        
        @note: The limit is only enforced on the public method, i.e. ask,
               get_related_lex_units, and not on the private methods. 
               Also note that this not affect test_lex_units_relation.
        """
        # because the bidirectional search seems to me much less sensitive 
        # to deep searches, probably beacuse it doesn't store all the paths
        if 0 < max_depth < 10:
            self._max_depth = max_depth
        else:
            raise ValueError("not a valid value for maximal depth: %s "
                             "(should be between 1 and 9 included)" % max_depth)

    
    # ------------------------------------------------------------------------------        
    # Semi-private methods
    # ------------------------------------------------------------------------------ 
    
    # parsing specifications

    def _split_query(self, query):
        query = query.strip().split() + 3 * [""]
        # relation are always in upper case
        query[1] = query[1].upper()
        return query[:3]
    
    
    def _split_unit_spec(self, spec):
        spec = spec + 2 * self._unit_separator
        return spec.strip().split(self._unit_separator)[:3]
    
    
    def _split_rel_spec(self, spec):
        if spec[-1] in "123456789":
            name, depth = spec[:-1], int(spec[-1])
        elif spec[-1] == "+":
            name, depth  = spec[:-1], 9
        else:
            name, depth = spec, 1
            
        return name.upper(), depth

        
    # search
    
    def _transitive_closure(self, lus, rel_name):
        """
        Computes the transitive closure of a set of lexical units
        over a certain relation. Returns a dict with successors as keys 
        and their distance (in edges) to the orginal lexical units.
        """
        assert isinstance(lus, list), repr(lus) + " is not a list"
        queue = lus
        lus = dict.fromkeys(lus)
        next_queue = []
        # distance of lu in queue to original lus
        distance = 0 
        successors= {}
        
        while queue:
            out_edges = self._graph.out_edges_iter(queue, data=True)
                
            for from_lu, to_lu, edge in out_edges:
                if ( self._rel_has_name(edge, rel_name) and
                     to_lu not in successors):
                    successors[to_lu] = distance + 1
                    
                    # A lexical unit from the original lus may be reached, and
                    # is indeed a valid successor, but should not be added to
                    # the queue otherwise we run in an endless loop
                    if to_lu not in lus:
                        next_queue.append(to_lu)
                    
            queue, next_queue = next_queue, []
            distance += 1
            
        return successors

    
    def _bidirectional_shortest_path(self, from_lus, to_lus, rel_name, depth):
        # Does BFS from both source and target and meets in the middle
        # Based on _bidirectional_pred_succ in networkx/path.py
        # Returns (pred, succ, w) where
        # pred is a dictionary of predecessors from w to the source, and
        # succ is a dictionary of successors from w to the target.
        
        # predecesssor and successors in search
        # keys are lexical units, values are tuples of lexcial units  and relations
        pred = dict.fromkeys(from_lus, (None, None))
        succ = dict.fromkeys(to_lus, (None, None))
        
        # check trivial case where sources and targets intersect
        for lu in from_lus:
            if lu in succ: 
                return None, lu, None

        # initialize fringes, start with forward
        forward_fringe = list(from_lus) 
        reverse_fringe = list(to_lus)
        level = 0        
    
        while forward_fringe and reverse_fringe and level != depth:
            this_level = forward_fringe
            forward_fringe = []

            out_edges = self._graph.out_edges_iter(this_level, data=True)
            
            for from_lu, to_lu, edge in out_edges:
                if self._rel_has_name(edge, rel_name):
                    if to_lu not in pred: # prevent cycles
                        forward_fringe.append(to_lu)
                        # If there are multiple matching edges,
                        # the previous dict value may be overwritten, 
                        # but we don't care because we are looking for *a* path
                        # instead of *all* paths.
                        pred[to_lu] = (from_lu, edge)
                    if to_lu in succ:  return pred, to_lu, succ # found path
                    
            level += 1
            if level == depth: break # max search depth reached

            this_level = reverse_fringe
            reverse_fringe = []
            
            in_edges = self._graph.in_edges_iter(this_level, data=True)
            
            for from_lu, to_lu, edge in in_edges:
                if self._rel_has_name(edge, rel_name):
                    if from_lu not in succ:
                        # may replace existing relation
                        succ[from_lu] = (to_lu, edge)
                        reverse_fringe.append(from_lu)
                    if from_lu in pred:  return pred, from_lu, succ # found path
                    
            level += 1
            
        return None, None, None  # no path found
    
    
    def _reconstruct_path(self,  pred, common_lu, succ, format=None):
        lu_formatter = self._get_lex_unit_formatter(format)
        rel_formatter = self._get_relation_formatter(format)
        
        if not pred and not succ:
            if common_lu:
                # trivial path because source and target nodes intersect
                return [lu_formatter(common_lu)]
            else:
                # no path found
                return []

        path = []
        lu = common_lu
        
        # from common lu to target lu
        while lu is not None:
            path.append(lu_formatter(lu))
            lu, edge = succ[lu]
            if edge is not None: 
                path.append(rel_formatter(edge)) 
            
        # from source lu to common
        lu, edge = pred[common_lu]
        path.insert(0, rel_formatter(edge))
        
        while lu is not None:
            path.insert(0, lu_formatter(lu))
            lu, edge = pred[lu]
            if edge is not None: 
                path.insert(0, rel_formatter(edge))
            
        return path
    
    
    def _search_related_lex_units(self, from_lu, rel_name, depth, lu_formatter,
                                  rel_formatter, path=[]):
        from_lu_related = {}
        
        if len(path) <= depth:
            for from_lu, to_lu, edge in self._graph.out_edges_iter(from_lu, data=True):
                if ( to_lu not in path and
                     self._rel_has_name(edge, rel_name)): 
                    to_lu_related = \
                    self._search_related_lex_units(to_lu, rel_name, depth,
                                                   lu_formatter, rel_formatter, 
                                                   path + [to_lu])
                    
                    to_lu_repr = lu_formatter(to_lu)
                    rel_repr = rel_formatter(edge)
                    
                    try:
                        from_lu_related[rel_repr][to_lu_repr] = to_lu_related
                    except KeyError:
                        from_lu_related[rel_repr] = {to_lu_repr: to_lu_related}
                                
        return from_lu_related
    
                          
    # lexical unit formatting
    
    def _get_lex_unit_formatter(self, format=None):
        if not format: format = self._output_format
        
        if format == "spec":
            return self._lu_to_spec
        elif format == "xml":
            return tostring
        elif format == "raw":
            return lambda lu: lu
        else:
            raise ValueError("unknown output format: " + format)

        
    def _lu_to_spec(self, lu):
        return self._unit_separator.join((
            self._get_lu_form(lu),
            self._get_lu_cat(lu),
            self._get_lu_sense(lu) ))
    
    
    # relation formatting
    
    def _get_relation_formatter(self, format=None):
        if not format: format = self._output_format
        
        if format == "xml":
            return tostring
        elif format == "spec":
            return self._rel_to_spec
        elif format == "raw":
            return lambda lu: lu
        else:
            raise ValueError("unknown output format: " + format)
        
        
    def _rel_to_spec(self, edge):
        return edge.get("relation")
    
    
    def _rel_to_xml(self, edge):
        return '<relation relation_name="%s">' % edge.get("relation")
        

    # synset formatting
    
    def _get_synset_formatter(self, format=None):
        if not format: format = self._output_format
        
        if format == "spec":
            return self._synset_to_specs
        elif format == "xml":
            return tostring
        elif format == "raw":
            return lambda lu: lu
        else:
            raise ValueError("unknown output format: " + format)

        
    def _synset_to_specs(self, synset):
        specs = []
        # REMOVE-ME: a list a synonym lu id's, because cdb is still buggy and
        # sometimes targets the same lu multiple times
        seen_lu_ids = []
        
        for syn in synset.find("synonyms") or []:
            c_lu_id = syn.get("c_lu_id")
            try:
                lu = self._c_lu_id2lu[c_lu_id]
            except KeyError:
                # no lu with this id
                continue

            if c_lu_id not in seen_lu_ids:
                specs.append(self._lu_to_spec(lu))
                seen_lu_ids.append(c_lu_id)
            
        return specs
    
    
    # <cdb_lu> accessors
    
    def _get_lu_form(self, lu):
        try:
            return lu.find("form").get("form-spelling", "") 
        except AttributeError:
            # <form> not found
            return ""
    
    
    def _get_lu_cat(self, lu):
        try:
            return lu.find("form").get("form-cat", "") 
        except AttributeError:
            # <form> not found
            return ""
    
    
    def _get_lu_sense(self, lu):
        return lu.get("c_seq_nr", "")
        
    
    def _lu_has_cat(self, lu, cat):
        try:
            # value of "form-cat" can be "noun"/"NOUN"
            return not cat or lu.find("form").get("form-cat").lower() == cat
        except AttributeError:
            # <form> not found
            return ""
    
    
    def _lu_has_sense(self, lu, sense):
        return not sense or lu.get("c_seq_nr") == sense

    
    # <relations> accessors
    
    def _get_rel_name(self, edge):
        return edge.get("relation") 
    
    
    def _rel_has_name(self, edge, name):
        return not name or edge.get("relation") == name 
        
    

    
# Debugging code

# Parsing cdb takes a long time. Therefore debugging is much faster if we
# parse just once, like this:
#
# >>> import cornetto.cornet as cornet
# >>> cornet._parse()
#    
# While debugging we inject the tables and graph in a Cornet instance:
# 
# >>> reload(cornet); c = cornet._get_cornet_instance()
#
    
    
#def _parse(cdb_lu="cdb_lu_minimal.xml", cdb_syn="cdb_syn_minimal.xml"):
    #global form2lu, c_lu_id2lu, c_sy_id2synset, graph
    #form2lu, c_lu_id2lu, c_sy_id2synset, graph = parse_cdb(cdb_lu, cdb_syn, verbose=True)
    

#def _get_cornet_instance():
    #c = Cornet()
    #c._form2lu = form2lu
    #c._c_lu_id2lu = c_lu_id2lu
    #c._c_sy_id2synset =  c_sy_id2synset
    #c._graph = graph
    #return c

#def _dump_multi_edges(c):
    #edges = c._graph.edges_iter()
    
    #while True:
        #try:
            #lu1, lu2 = edges.next()
        #except StopIteration:
            #break
        
        #d = c._graph[lu1][lu2]
        
        #if len(d) > 1:
            #relations = [d2["relation"] for d2 in d.values()]
            #print c._lu_to_spec(lu1), ",".join(relations), c._lu_to_spec(lu2)
        
            #for i in range(len(d) - 1):
                #edges.next()

