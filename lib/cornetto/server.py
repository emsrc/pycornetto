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
socket server exposing Cornetto database through XML-RPC
"""

# TODO:

# FEATURES
# - logging queries
# - a forking/threading server


__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'

from sys import stderr
from textwrap import wrap
from SimpleXMLRPCServer import SimpleXMLRPCServer
from cornetto.cornet import Cornet


class CornetProxy(object):
    """
    A proxy to the Cornet class which serves to:
    
        1. hide Cornet methods which should not be exposed through XML-RPC
        2. restrict parameter values which should not be exposed through 
           XML-RPC (e.g. "raw" format)
        3. translate None return values, which XML-RPC cannot handle, 
           to False
        4. provide doc strings which are suitable to XML-RPC's 
           system.methodHelp command
           
    Note that this proxy class should be not used by other Python programs,
    which should call methods from the Cornet class directly. 
    """
    
    _allowed_formats = ("spec", "xml", None)
    
    
    def __init__(self, cdb_lu, cdb_sy, verbose=False, max_depth=None,
                 cornet_class=Cornet):
        self._cornet = cornet_class()
        # use separate call to set max depth, 
        # because None is not a valid default value
        # FIXME: crappy solution
        if max_depth is not None: self._cornet.set_max_depth(max_depth)
        self._cornet.open(cdb_lu, cdb_sy, verbose)
        

    def help(self, method=None):
        """
        help([METHOD]) --> HELP
        
        Return short description of all available methods, 
        or full help on a particular method.
        
        Parameters:       

            METHOD string: method name
            
            HELP string: help text
            
        Remarks:
            
            This is a fancy replacement for XML-RPC's introspection methods
            system.listMethods, system.methodHelp, which are still available
            (system.methodSignature is not supported).
        """
        if method:
            return self._describe_method(method)
        else:
            return self._summarize_all_doc_strings()
    
    
    def help_specs(self):
        """
        help_specs() --> HELP
        
        Help on writing specifications for lexical units and relations
        
        Parameters:       
        
            HELP string: help text
        """
        return _help_specs_text
    
    
    def help_formats(self):
        """
        help_formats() --> HELP
        
        Help on output formats
        
        Parameters:       
        
            HELP string: help text
        """
        return _help_formats_text
        
        
    def ask(self, query, format=None):
        """
        ask(QUERY[, FORMAT]) --> ANSWER
        
        Pose a query about lexical units to the Cornetto database
        
        Parameters:       
        
            QUERY string:  a specification of lexical units(s) and relations
            FORMAT string: output format ("spec" or "xml")     
            
            ANSWER array/struct/boolean: answer to query 
                                          or False
                                          
        Remarks:
            
            This function is the most general and convenient way to interact
            with Cornetto. It supports three different types of queries:
            
                1. Getting lexical units
                
                   If the query consists of only a lexical unit specification
                   the answer lists all lexical units which satisfy this
                   specification. See also function "get_lex_units"
                
                2. Getting related lexical units
                
                   If the query consists of a lexical unit specification plus
                   a relation specification, the answer consists of all
                   lexical units related by the specified relation(s). See
                   also function "get_related_lex_units"
                
                3. Testing relations between lexical units
                
                   If the query consists of a lexical unit specification, plus
                   a relation specification plus another lexical
                   specification, the answer is a path from the first to the
                   second lexical unit(s) along the specified relation(s). See
                   also function "test_lex_units_relation"                   
        """
        return self._safe_return(
            self._cornet.ask(query, 
                             self._safe_format(format)))
        

    def get_lex_units(self, spec, format=None):
        """
        get_lex_units(SPEC[, FORMAT]) --> LUS

        Get all lexical units which satisfy this specification
        
        Parameters:       
        
            SPEC string: lexical unit specification
            FORMAT string: output format ("spec" or "xml")  
            
            LUS array: list of lexical units, possibly empty.
    
        Examples (output in Python format):
            
            $ get_lex_units("lamp")
            ['lamp:noun:3', 'lamp:noun:4', 'lamp:noun:1', 'lamp:noun:2']
            
            $ get_lex_units("varen")
            ['varen:verb:3', 'varen:noun:1', 'varen:verb:1', 'varen:verb:2']
    
            $ get_lex_units("varen:noun")
            ['varen:noun:1']
    
            $ get_lex_units("varen:verb:3")
            ['varen:verb:3']
    
            $ inst.get_lex_units("varen:noun:3")
            []
        """
        return self._safe_return(
            self._cornet.get_lex_units(spec, 
                                       self._safe_format(format)))
        
        
    def get_related_lex_units(self, lu_spec, rel_spec, format=None):
        """
        get_related_lex_units(LU_SPEC, REL_SPEC[, FORMAT]) --> RESULT
        
        For all specified lexical units, find all lexical units related 
        by the specified relation.
        
        Parameters:       
        
            LU_SPEC string: lexical unit(s) specification of source
            REL_SPEC string: relation(s) specification
            FORMAT string: output format ("spec" or "xml")       
            
            RESULT struct: related lexical units 
            
        Remarks:
            
            The format of the return value is a hierarchical struct. The keys
            are lexical units and relations. The values values are (empty)
            structs.
            
        Examples (output in Python format):
            
            $ get_related_lex_units("slang", "SYNONYM")
            {'slang:noun:1': {'SYNONYM': {'serpent:noun:2': {}}},
             'slang:noun:2': {},
             'slang:noun:3': {'SYNONYM': {'pin:noun:2': {}, 'tang:noun:2': {}}},
             'slang:noun:4': {'SYNONYM': {'groepstaal:noun:1': {},
                                          'jargon:noun:1': {},
                                          'kringtaal:noun:1': {}}},
             'slang:noun:5': {'SYNONYM': {'muntslang:noun:1': {}}},
             'slang:noun:6': {'SYNONYM': {'Slang:noun:1': {}}}}
    
            $ get_related_lex_units("slang::1", "1")
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
                              'SYNONYM': {'serpent:noun:2': 
        """        
        return self._safe_return(
            self._cornet.get_related_lex_units(lu_spec,
                                               rel_spec,
                                               self._safe_format(format)))
        
    
    def test_lex_units_relation(self, from_lu_spec, rel_spec, to_lu_spec, format=None):
        """
        test_lex_units_relation(FROM_LU_SPEC, REL_SPEC, TO_LU_SPEC[, FORMAT]) --> PATH
        
        Test if certain relation(s) hold between certain lexical units
        
        Parameters:       
        
            FROM_LU_SPEC string: lexical unit specification of the source(s)
            REL_SPEC string: relation(s) specification
            TO_LU_SPEC string: lexical unit specification of the target(s)
            FORMAT string: output format ("spec" or "xml")       
            
            PATH array: a path from any of the source lexical units to any of the 
                          target lexical unit(s) along one or more of the specified
                          relation(s), possibly empty
                          
        Remarks:
            
            The result may not be the only shortest path.
            
        Examples (output in Python format):
            
            $ test_lex_units_relation("lamp", "HAS_HYPONYM", "gloeilamp")
            ['lamp:noun:2', 'HAS_HYPONYM', 'gloeilamp:noun:1']
            
            $ test_lex_units_relation("lamp", "HAS_HYPONYM2", "fotolamp")
            ['lamp:noun:2', 'HAS_HYPONYM', 'gloeilamp:noun:1', 'HAS_HYPONYM', 'fotolamp:noun:1']
            
            $ test_lex_units_relation("lamp", "HAS_HYPONYM", "fotolamp")
            []
        """    
        return self._safe_return(
            self._cornet.test_lex_units_relation(from_lu_spec,
                                                 rel_spec,
                                                 to_lu_spec,
                                                 self._safe_format(format)))
            
    
    def get_synsets(self, spec, format=None):
        """
        get_synsets(SPEC[, FORMAT]) --> SETS
        
        Get all synsets containing lexical units which satisfy a certain specification.
        
        Parameters:       
      
            SPEC string: lexical unit specification
            FORMAT string: output format ("spec" or "xml")        
            
            SETS array: list of synsets, possibly empty
    
        Examples (output in Python format):
    
            $ get_synsets("slang")
            [['Slang:noun:1', 'slang:noun:6'],
             ['slang:noun:5', 'muntslang:noun:1'],
             ['slang:noun:1', 'serpent:noun:2'],
             ['slang:noun:2'],
             ['tang:noun:2', 'pin:noun:2', 'slang:noun:3'],
             ['jargon:noun:1', 'groepstaal:noun:1', 'kringtaal:noun:1', 'slang:noun:4']]
             
             $ get_synsets("slang:noun:5")
             [['slang:noun:5', 'muntslang:noun:1']]
    
             $ get_synsets("slang:noun:7")
             []
        """  
        return self._safe_return(
            self._cornet.get_synsets(spec,
                                     self._safe_format(format)))
    
        
    def get_related_synsets(self, lu_spec, rel_name=None, format=None):
        """
        get_related_synsets(LU_SPEC[, REL_NAME[, FORMAT]]) --> RESULT
        
        For all synsets containing lexical units satisfying this specification
        find the related synsets along this relation. 
        
        Parameters:       

            LU_SPEC string: lexical unit(s) specification of source
            REL_NAME string: relation name; if no relation is given, 
                all relations are considered.
            FORMAT string: output format ("spec" or "xml")   
            
            RESULT struct: a struct with relations as keys and arrays 
                of synsets as value, possibly empty
                
        Remarks:
            
            Note that REL_NAME is a relation name, not a relation
            specification, and that search is thus not transitive.
            
        Examples (output in Python format):
              
            $ get_related_synsets("lamp", "HAS_HYPERONYM")
            {'HAS_HYPERONYM': [['armatuur:noun:1', 'verlichtingsarmatuur:noun:1'],
                               ['lamp:noun:2', 'licht:noun:13', 'lichtje:noun:1'],
                               ['lichtbron:noun:1'],
                               ['voorwerp:noun:1', 'ding:noun:1']]}
            
            $ get_related_synsets("slang::1")
            {'HAS_HOLO_MEMBER': [['slangegebroed:noun:1', 'slangengebroed:noun:2']],
             'HAS_HYPERONYM': [['reptiel:noun:1']],
             'HAS_MERO_PART': [['slangekop:noun:1', 'slangenkop:noun:1']]}
        """
        return self._safe_return(
            self._cornet.get_related_lex_units(lu_spec,
                                               rel_name,
                                               self._safe_format(format)))
        
  
    def get_lex_unit_by_id(self, c_lu_id, format=None):
        """
        get_lex_unit_by_id(C_LU_ID[, FORMAT]) --> LU
        
        Get lexical unit by id
        
        Parameters:       
        
            C_LU_ID string: value of the 'c_lu_id' attribute 
                at <cdb_lu> element
            FORMAT string: output format ("spec" or "xml")   
            
            LU string/boolean: lexical unit in the requested output format, 
                   or False
        """      
        return self._safe_return(
            self._cornet.get_lex_unit_by_id(c_lu_id,
                                            self._safe_format(format)))

        
    def get_synset_by_id(self, c_sy_id, format=None):
        """
        get_synset_by_id(C_SY_ID[,FORMAT]) --> SET
        
        Get synset by id
        
        Parameters:       
        
            C_SY_ID string: value of the 'c_sy_id' attribute 
                at <cdb_synset> element
            FORMAT string: output format ("spec" or "xml")   
            
            SET array/boolean: set of lexical units in the requested 
                output format, or False
        """   
        return self._safe_return(
            self._cornet.get_synset_by_id(c_sy_id,
                                          self._safe_format(format)))
    
    
    def all_common_subsumers(self, lu_spec1, lu_spec2,
                             rel_name="HAS_HYPERONYM", format=None):
        """
        all_common_subsumers(LU_SPEC_1, LU_SPEC_2[, rel_name="HAS_HYPERONYM"[, format=None]]) 
        --> RESULT
                   
        Find all common subsumers of two lexical units over the given relation. 
        
        Parameters:       
        
            This method will only make sense for some relations (typically HAS_HYPERONYM) 
            but not for others (like SYNONYM).
            
            LU_SPEC_1 string: first lexical unit specification
            LU_SPEC_2 string: second lexical unit specification
            REL_NAME string: relation name
            FORMAT string: output format ("spec" or "xml")
            
            RESULT struct: a struct with path lenghts as key and lists of 
                common subsumers as values, possibly empty
        
        Remarks:
        
            The common subsumers are grouped according to the lenght of the
            path (in edges) from the first lexical unit to the subsumer to the
            second lexical unit.
        
        Examples (output in Python format):
            
            $ all_common_subsumers("man", "vrouw")
            {1: ['man:noun:3'],
             2: ['levenspartner:noun:1',
                 'wederhelft:noun:1',
                 'figuur:noun:4',
                 'partner:noun:4',
                 'persoon:noun:1',
                 'mens:noun:4'],
             3: ['ziel:noun:3',
                 'mensenkind:noun:1',
                 'mens:noun:1',
                 'sterveling:noun:1',
                 'homo sapiens:noun:1'],
             5: ['zoogdier:noun:1'],
             7: ['dier:noun:1', 'gedierte:noun:2', 'beest:noun:1'],
             9: ['organisme:noun:2'],
             10: ['object:noun:1'],
             11: ['creatuur:noun:1', 'wezen:noun:1', 'schepsel:noun:1'],
             12: ['iets:noun:2']}
        """
        # keys must be strings in XMLRPC, so convert int to str
        d1 = self._cornet.all_common_subsumers(lu_spec1, lu_spec2, rel_name, 
                                               self._safe_format(format))
        d2 = dict([ (str(k), v) 
                    for k,v in d1.items() ]) 
        
        return self._safe_return(d2)
    
    
    def least_common_subsumers(self, lu_spec1, lu_spec2,
                               rel_name='HAS_HYPERONYM', format=None):
        """
        least_common_subsumers(LU_SPEC_1, LU_SPEC_2[, rel_name="HAS_HYPERONYM"[, format=None]]) 
        --> RESULT
                               
        Finds the least common subsumers of two lexical units over the given
        relation, that is, those common subsumers of which the lenght of
        the path (in edges) from the first lexical unit to the subsumer to the
        second lexical unit is minimal.
        
        Parameters:       
            
            LU_SPEC_1 string: first lexical unit specification
            LU_SPEC_2 string: second lexical unit specification
            REL_NAME string: relation name
            FORMAT string: output format ("spec" or "xml")
            
            RESULT array:  a lists of the least common subsumers, possibly empty
        
        Remarks:
        
            This method will only make sense for some relations (typically HAS_HYPERONYM) 
            but not for others (like SYNONYM).
            
        Examples (output in Python format):
            
            $ least_common_subsumers("auto", "fiets"))
            ['vehikel:noun:1', 'voertuig:noun:1']
        """
        return self._safe_return(
            self._cornet.least_common_subsumers(lu_spec1, lu_spec2, rel_name, 
                                                self._safe_format(format)))
    
        
    # private methods
        
    def _safe_return(self, value):
        """
        translates None return values, which XML-RPC cannot handle, to False
        """
        if value is None:
            return False
        elif type(value) is type([]):
            return [self._safe_return(e) 
                    for e in value]
        elif type(value) is type({}):
            return dict( (self._safe_return(k), self._safe_return(v))
                         for k,v in value.items() )
        else:
            return value
        
        
    def _safe_format(self, format):
        if format in self._allowed_formats:
            return format
        else:
            raise ValueError("unknown output format: %s" % format)
        

    def _describe_method(self, method):
        if not method.startswith("_") and hasattr(self, method):
            return getattr(self, method).__doc__
        else:
            raise ValueError("no method called: " + method)
            
        
    def _summarize_all_doc_strings(self): 
        text = ""
        
        for attr in dir(self):
            if not attr.startswith("_"):
                method = getattr(self, attr)
                text += self._summarize_doc_string(method)
                
        return text
    
        
    def _summarize_doc_string(self, method):
        doc = method.__doc__
        lines = doc.split("\n")
        text = lines[1].strip() + "\n"
        
        for l in lines[3:]:
            if l.strip():
                text += l + "\n"
            else:
                break

        return text + "\n"
    
    


def start_server(cdb_lu, cdb_syn, host="localhost", port=5204, log=None,
                 verbose=False, max_depth=None, similarity=False, proxy_class=None):
    """
    main function to start the Cornetto XMLRPC server
    
    @param cdb_lu: xml definition of the lexical units
    @type cdb_lu: file or filename
    
    @param cdb_syn:xml definition of the synsets
    @type cdb_syn: file or filename

    @keyword host: host to listen on
    @type host: string
    
    @keyword port: port to listen on
    @type port: int
    
    @keyword log: log requests  
    @type log: bool
    
    @keyword verbose: verbose output during parsing    
    @type verbose: bool

    @keyword max_depth: maximal search depth (between 1 and 9)
    @type max_depth: int
    
    @keyword similarity: extend interface with word similarity measures
        from SimCornet (requires cdb_lu file with counts)
    @type similarity: bool
    
    @keyword proxy_class: class that serves as proxy to (a subclass of) 
        the Cornet class (e.g. CornetProxy or SimCornetProxy)
    @type proxy_class: (subclass of) CornetProxy
    """
    print >>stderr, "Reading Cornetto database - this may take a while..."
    
    if similarity:
        from cornetto.simserver import SimCornetProxy
        proxy_class = SimCornetProxy
    elif proxy_class:
        assert issubclass(proxy_class, CornetProxy)
    else:
        proxy_class = CornetProxy
    
    cornet = proxy_class(cdb_lu, cdb_syn, verbose, max_depth)
    
    server = SimpleXMLRPCServer((host, port), logRequests=log, encoding="UTF-8")
    server.register_introspection_functions()
    server.register_function(echo)
    server.register_instance(cornet)
    
    print >>stderr, "Listening on %s:%d" % (host, port)
    server.serve_forever()
    
    
    

def echo(s):
    """
    simply returns the input (useful for testing the socket connection)
    """
    return s
    

_help_specs_text = """
Most methods require input in the form of a shorthand for
specifying lexical units and relations, as described below.


*** Lexical units specifications ***

A specification of lexical units consists of three parts, separated by 
a single colon (':') character:

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


*** Relation specifications ***

A specification of a relation consists of two parts:

1. Relation name (optional)

   The name of a Wordnet relation between two synsets.
   See the Cornetto documentation for the available relations.
   If not given, all relations are tried.
   The special relation "SYNONYM" holds between all members of the same synset.
   The relation name is not case-sensitive; you can use lower case.

2. Depth (optional)

   A digit ('0' to '9') or the plus sign ('+').
   This represents the depth of the relations that are considered during search.
   In other words, the maximal number of links allowed.
   If not given a default value of 1 is used.
   The plus represents the system maximum (currently 9). 
   
A relation specification must have a name, a depth or both. Valid relation
specification include:

   - HAS_HYPERONYM
   - HAS_HYPERONYM1
   - HAS_HYPERONYM+
   - 3
   - +
"""


_help_formats_text = """"
Lexical units and relations can be returned in several formats.
The following formats are currently supported:

1. spec

   This is the same format used for specifying lexical units and relations.
   See function "help_specs()" for details.
   
2. xml

   This means that the original XML string is returned. 
"""


    
    
