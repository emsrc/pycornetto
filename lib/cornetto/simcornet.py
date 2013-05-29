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
an extension of the Cornet class which adds word similarity measures
"""

# TODO:
# - other similarity measures based on path lenght
# - units tests


__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'

from math import log

from cornetto.parse import parse_cdb_with_counts
from cornetto.cornet import Cornet


class SimCornet(Cornet):    
    """
    An extension of the Cornet class which adds word similarity measures.
    This assumes counts are added to the Cornetto database. 
    """
    
    # ------------------------------------------------------------------------------        
    # Public methods
    # ------------------------------------------------------------------------------  
    
    def open(self, cdb_lu, cdb_syn, verbose=False):
        """
        Open and parse Cornetto database files with counts
        
        @param cdb_lu: xml definition of the lexical units with counts
        @type cdb_lu: file or filename
        @param cdb_syn: xml definition of the synsets
        @type cdb_syn: file or filename
        @keyword verbose: verbose output during parsing
        """
        ( self._form2lu, 
          self._c_lu_id2lu,
          self._c_sy_id2synset, 
          self._graph,
          self._cat2counts ) = parse_cdb_with_counts(cdb_lu, cdb_syn, verbose)
        
    
    # counts

    def get_count(self, lu_spec, subcount=False, format=None):
        """
        Get (sub)counts for lexical units satisfying this specification
        
        >>> c.get_counts("varen")
        {'varen:noun:1': 434,
         'varen:verb:1': 15803,
         'varen:verb:2': 15803,
         'varen:verb:3': 15803}
        
        >>> pprint(c.get_counts("varen", subcount=True))
        {'varen:noun:1': 434,
         'varen:verb:1': 18977,
         'varen:verb:2': 62086,
         'varen:verb:3': 15803}
        
        @param lu_spec: lexical unit specification
        
        @keyword subcount: return subcounts instead of plain counts
        @type subcount: bool
        
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: mapping of lexical units in requested output format 
                 to (sub)counts
        @rtype: dict
        
        @note: As the counts are currently based on lemma plus part-of-speech, 
               not on the sense, they are the same for all senses of the 
               same category,
        """
        formatter = self._get_lex_unit_formatter(format)
        lu2count = dict()
        
        for lu in self.get_lex_units(lu_spec, "raw"):
            lu2count[formatter(lu)] = self._get_lu_count(lu, subcount)
            
        return lu2count
    
    
    def get_total_counts(self):
        """
        Get the total counts per category and overall
        
        The categories are "noun", "verb", "adj", "other";
        "all" represents the overall count.
        
        >>> c.get_total_counts()
        {'adj': 62156445,
         'all': 518291832,
         'noun': 187143322,
         'other': 199269966,
         'verb': 69722099}
        
        @return: mapping of categories to counts
        @rtype: dict
        """
        return self._cat2counts
    
    
    # statistics
    
    def get_probability(self, lu_spec, subcount=False, smooth=False,
                        cat_totals=False, format=None):
        """
        Get probability (p) for lexical units satisfying this specification,
        where the probability is defined as lu_count / total_count.
        
        By default, the total count is taken to be the sum of counts over all
        word forms in the Cornetto database. However, when comparing two words
        of the same category (nouns, verbs, adjectives) it may be more
        appropriate to take the sum over only the word forms of this category.
        This method is used if the keyword "cat_totals" is true.
        
        >>> c.get_probabilities("varen")
        {'varen:noun:1': 8.3736608066013281e-07,
         'varen:verb:1': 3.0490544176663777e-05,
         'varen:verb:2': 3.0490544176663777e-05,
         'varen:verb:3': 3.0490544176663777e-05}
        
        @param lu_spec: lexical unit specification
        @type lu_spec: string
        
        @keyword subcount: use subcounts instead of plain counts
        @type subcount: bool
        
        @keyword smooth: smooth counts by adding one to lexical units 
            with a zero count
        @type smooth: bool
        
        @keyword cat_totals: use total count for category of lexical unit
            instead of overall total count
        @type cat_totals: bool
        
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: mapping of lexical units in requested output format 
                 to probabilties
        @rtype: dict
        """
        formatter = self._get_lex_unit_formatter(format)
        lu2prob = {}
        
        for lu in self.get_lex_units(lu_spec, format="raw"):
            lu2prob[formatter(lu)] = self._p(lu, subcount, smooth, cat_totals)
            
        return lu2prob

           
    def get_info_content(self, lu_spec, subcount=False, smooth=False, cat_totals=False,
                         format=None):
        """
        Get information content (IC) for lexical units satisfying this
        specification, defined as the negative log of the lexical unit's
        probability, i.e. -log_2(lu_count / total_count)
        
        If a lexical unit has a count of zero, the probability is zero, the
        log is undefined, and None is returned. Unless the keyword "smooth" is
        true, in which case the count is smoothed by adding one.
        
        If no lexical unit matches the specification, an empty mapping is
        returned.
        
        >>> pprint(c.get_info_content("plant"))
        {'plant:noun:1': 14.51769181264614}
        
        >>> pprint(c.get_info_content("plant", subcount=True))
        {'plant:noun:1': 10.482770362490861}
        
        @param lu_spec: lexical unit specification
        @type lu_spec: string
        
        @keyword subcount: use subcounts instead of plain counts
        @type subcount: bool
        
        @keyword smooth: smooth counts by adding one to lexical units 
            with a zero count
        @type smooth: bool
        
        @keyword cat_totals: use total count for category of lexical unit
            instead of overall total count
        @type cat_totals: bool
        
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: mapping of lexical units in requested output format 
                 to information content
        @rtype: dict
        """
        formatter = self._get_lex_unit_formatter(format)
        lu2ic = {}
        
        for lu in self.get_lex_units(lu_spec, format="raw"):
            lu2ic[formatter(lu)] = self._IC(lu, subcount, smooth, cat_totals)
            
        return lu2ic
        
    
    # corpus-based similarity metrics
        
    def resnik_sim(self, lu_spec1, lu_spec2, smooth=False, cat_totals=False,
                   format=None):
        """
        Compute the semantic similarity as decribed in Philip Resnik's paper
        "Using Information Content to Evaluate Semantic Similarity in a
        Taxonomy" (1995). It is defined for a pair of concepts c1 and c2 as:
        
        argmax [IC(c1) + IC(c2) - 2 * IC(lcs)] for all lcs in LCS(c1, c2)
        
        In other words, the maximum value of the information content over all 
        least common subsumers of two concepts. An important point is that the 
        counts of an LCS, as used in computing its probabilty, is the sum of 
        its own count plus the counts of all concepts that it subsumes.
        
        As suggested by Resnik, it can be extended to _word_ similarity by
        taking the maximum over the scores for all concepts that are senses of
        the word. This means that if just two words are specified - without a
        category or sense - two sets of matching lexical units are retrieved.
        For every combination of lexical units from these two sets, the LCS is
        computed (if any), and the one with the maximum information content is
        selected.
        
        If no LCS is found, this can mean two things:        
            1. The two words have no LCS because they truely have nothing 
               in common. In this case we assume the LCS is zero and therefore 
               we return zero.
            2. The two words should have something in common, but the correct 
               LCS is not present in the Cornetto database. However, since 
               there is no way to know this, we consider this the same as (1),
               and zero is returned.
        
        There are two more marginal cases:
            1. No lexical units in the Cornetto database match the 
               specifications. 
            2. All LCS have a subcount of zero, and no smoothing was applied,
               so its IC is undefined. 
        In both cases None is returned.
        
        Notice that it is difficult to compare Resnik's word similarities,
        because they depend on the subcounts. With identical words, for instance,
        resnik_sim("iets", "iets") = 1.3113543459343666 whereas
        resnik_sim("spotje", "spotje") = 25.141834494846584

        @param lu_spec1: first lexical unit(s) specification
        @param lu_spec2: second lexical unit(s) specification
        
        @keyword smooth: smooth by adding one to lexical units with a zero count
        @type smooth: bool
        
        @keyword cat_totals: use total count for category of lexical unit
            instead of overall total count
        @type cat_totals: bool
        
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: similarity score greater than or equal to zero
        @rtype: float or None
        """
        max_sim = None
        
        # If no matching lex units were found, we return None        
        if self.get_lex_units(lu_spec1) and self.get_lex_units(lu_spec2):
            lcs_ics = [ self._IC(lcs, True, smooth, cat_totals)
                        for lcs in self.least_common_subsumers(lu_spec1, 
                                                               lu_spec2,
                                                               format="raw") ]
            if lcs_ics:
                # If all lcs have a subount of zero (or no "subcount" attrib),
                # then lcs_ics is [None, ..., None], and we return None,
                # because max[None, ..., None]() == None
                max_sim = max(lcs_ics)
            else:
                # Matching lex units do exist but have no lcs, which is
                # comparable to sharing only "the ultimate abstract", which
                # has an IC of zero, and therefore similarity is zero. In
                # reality, of course, the true lcs may simply be missing from
                # the db.
                max_sim = 0.0

        return max_sim
    
    
    def jiang_conrath_dist(self, lu_spec1, lu_spec2, smooth=False,
                           cat_totals=False, format=None):
        """
        Compute the semantic distance as decribed in Jay Jiang & David
        Conrath's paper "Semantic Similarity Based on Corpus Statistics and
        Lexical Taxonomy" (1997). It is defined for a pair of concepts c1 and
        c2 as:
        
        argmin [IC(c1) + IC(c2) - 2 * IC(lcs)] for all lcs in LCS(c1, c2)
        
        This is without the edge and node weighting scheme, which is not
        implemented here. The measure is extended to a _word_ distance measure
        by taking the minimum over the scores for all concepts (lexical units)
        that are senses of the word (cf. doc of resnik_sim).
        
        If no LCS is found, this can mean two things:        
            1. The two words have no LCS because they truely have nothing 
               in common. In this case we assume the LCS is zero and therefore 
               we return the minimun of IC(c1) + IC(c2).
            2. The two words should have something in common, but the correct 
               LCS is not present in the Cornetto database. However, since 
               there is no way to know this, we consider this the same as (1),
               and we return the minimun of IC(c1) + IC(c2).
        
        There are three more marginal cases:
            1. No lexical units in the Cornetto database match the 
               specifications.
            2. All matching lexical units have a subcount of zero,
               and no smoothing was applied, so their IC is undefined. 
            3. All LCS have a subcount of zero, and no smoothing was applied,
               so its IC is undefined. This implies that all subsumed
               lexical units must have a subcount of zero, and therefore
               (2) must be the case as well.  
        In all of these three cases None is returned.
        
        @param lu_spec1: first lexical unit(s) specification
        @param lu_spec2: second lexical unit(s) specification
        
        @keyword smooth: smooth by adding one to lexical units with a zero count
        @type smooth: bool
        
        @keyword cat_totals: use total count for category of lexical unit
            instead of overall total count
        @type cat_totals: bool
        
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: distance greater than of equal to zero
        @rtype: float or None
        """
        # It is tempting to simply call self.least_common_subsumers(lu_spec1,
        # lu_spec2), but that would return _all_ lcs. However, since lu_spec1
        # and lu_spec2 may be underspecified, they may both refer to sets of
        # lexical units. Not every returned lcs is neccessarily also a true
        # lcs for all the combinations of these lexical units. For these
        # cases, the calculation of ic1 + ic2 - 2 * lcs_ic would be invalid.
        
        lus1 = self.get_lex_units(lu_spec1, format="raw")
        lus2 = self.get_lex_units(lu_spec2, format="raw")
        
        min_dist = None
        
        # TODO: can be optimized in several ways, e.g.
        # transtive_closure and IC's for lu2 are calculated multiple times 
        for lu1 in lus1:
            ic1 = self._IC(lu1, True, smooth, cat_totals)
            if ic1 is None:
                # zero count or no "subcount" attrib found 
                continue
            
            for lu2 in lus2:
                ic2 = self._IC(lu2, True, smooth, cat_totals)
                if ic2 is None:
                    # zero count or no "subcount" attrib found 
                    continue
                
                # hmmm, conversion back to spec stinks
                for lcs in self.least_common_subsumers(self._lu_to_spec(lu1),
                                                       self._lu_to_spec(lu2),
                                                       format="raw"):
                    lcs_ic = self._IC(lcs, True, smooth, cat_totals)
                    if lcs_ic is None:
                        # No "subcount" attrib found - this should never happen
                        # Note that the subcount cannot be zero, as in that case
                        # the subcounts of all subsumed lexical units, including
                        # lu1 and lu2, must be zero as well. 
                        continue
                    
                    new_dist = ic1 + ic2 - 2 * lcs_ic
                    
                    # cannot use not "min_dist" here, because min_dist may be zero!
                    # cannot use min() here, because min(0, None) == None
                    if min_dist is None or new_dist < min_dist:
                        min_dist = new_dist
                    
                # At this point we are sure that we have valid ic1 and ic2.
                # If no lcs was found, we assume lcs_ic is zero, 
                # and thus the sim score is ic1 + ic2.
                new_dist = ic1 + ic2
                
                if min_dist is None or new_dist < min_dist:
                    min_dist = new_dist
                        
        return min_dist
    
    
    def jiang_conrath_sim(self, lu_spec1, lu_spec2, smooth=False,
                           cat_totals=False, format=None):
        """
        Returns Jiang & Conrath's distance converted to a similarity
        by means of sim = 1 / (1 + dist). See jiang_conrath_dist
        
        If the distance is None, so is the similarity.
        
        The translation from distance to similarity is not uniform. That is,
        the space between the distances 1 and 2 and between the distances 2
        and 3 is the same (i.e. 1), but the space between the corresponding
        similaraties, i.e. between 0.5 and 0.33 and between 0.33 and 0.25, is
        not.
        
        @param lu_spec1: first lexical unit(s) specification
        @param lu_spec2: second lexical unit(s) specification
        
        @keyword smooth: smooth by adding one to lexical units with a zero count
        @type smooth: bool
        
        @keyword cat_totals: use total count for category of lexical unit
            instead of overall total count
        @type cat_totals: bool
        
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: similarity score between zero and one included.
        @rtype: float or None
        """
        sim = self.jiang_conrath_dist(lu_spec1, lu_spec2, smooth, cat_totals,                           
                                      format)
        # sim is None if no matching lexical units were found,
        # or if any of thenm have a (sub)count of zero
        if sim is not None:
            return 1 / ( 1 + sim)
    
    
    def lin_sim(self, lu_spec1, lu_spec2, smooth=False, cat_totals=False,
                format=None):
        """
        Compute the semantic similarity as decribed in the paper Dekang Lin's 
        paper "An information-theoretic definition of similarity" (1998).
        It is defined for a pair of concepts c1 and c2 as:
        
        argmax [2 * IC(lcs) / (IC(c1) + IC(c2))] for all lcs in LCS(c1, c2)
        
        This measure is extended to a _word_ distance measure by taking the
        maximum over the scores for all concepts (lexical units) that are
        senses of the word (cf. doc of resnik_sim).
        
        If no LCS is found, this can mean two things:        
            1. The two words have no LCS because they truely have nothing 
               in common. In this case we assume the IC of the LCS is zero and
               we return zero.
            2. The two words should have something in common, but the correct 
               LCS is not present in the Cornetto database. However, since 
               there is no way to know this, we consider this the same as (1),
               and we return zero.
               
        There are three more marginal cases:
            1. No lexical units in the Cornetto database match the 
               specifications. 
            2. All matching lexical units have a subcount of zero,
               and no smoothing was applied, so their IC is undefined. 
            3. All LCS have a subcount of zero, and no smoothing was applied,
               so its IC is undefined. This implies that all subsumed
               lexical units must have a subcount of zero, and therefore
               (2) must be the case as well.  
        In all of these three cases None is returned.
        
        
        @param lu_spec1: first lexical unit(s) specification
        @param lu_spec2: second lexical unit(s) specification
        
        @keyword smooth: smooth by adding one to lexical units with a zero count
        @type smooth: bool
        
        @keyword cat_totals: use total count for category of lexical unit
            instead of overall total count
        @type cat_totals: bool
        
        @keyword format: output format
        @type format: 'spec', 'xml', 'raw'
        
        @return: similarity score between zero and one included
        @rtype: float or None
        """
        # this is alomst identical to jiang_conrath_dist
        lus1 = self.get_lex_units(lu_spec1, format="raw")
        lus2 = self.get_lex_units(lu_spec2, format="raw")
        
        max_sim = None
        
        for lu1 in lus1:
            ic1 = self._IC(lu1, True, smooth, cat_totals)
            if ic1 is None:
                # zero count or no "subcount" attrib found  
                continue
            
            for lu2 in lus2:
                ic2 = self._IC(lu2, True, smooth, cat_totals)
                if ic2 is None: 
                    # zero count or no "subcount" attrib found 
                    continue
                
                for lcs in self.least_common_subsumers(self._lu_to_spec(lu1),
                                                       self._lu_to_spec(lu2),
                                                       format="raw"):
                    lcs_ic = self._IC(lcs, True, smooth, cat_totals)
                    if lcs_ic is None: 
                        # No "subcount" attrib found - this should never happen
                        # Note that the subcount cannot be zero, as in that case
                        # the subcounts of all subsumed lexical units, including
                        # lu1 and lu2, must be zero as well. 
                        continue
                    
                    new_sim = (2 * lcs_ic) / float(ic1 + ic2)
                    max_sim = max(max_sim, new_sim)
                    
                # At this point we are sure that we have valid ic1 and ic2.
                # If no lcs was found, we assume lcs_ic is zero, 
                # and thus the sim score is zero.
                # Hence,  without any max_sim yet, we assume max_sim is zero. 
                max_sim = max(max_sim, 0.0)
                        
        return max_sim
    
        
    # ------------------------------------------------------------------------------        
    # Semi-private methods
    # ------------------------------------------------------------------------------ 
    
    def _get_lu_count(self, lu, subcount=False):
        """
        get (sub)count of lexical unit
        """
        try:
            if subcount:
                return int(lu.find("form").get("subcount"))
            else:
                return int(lu.find("form").get("count"))
        except AttributeError:
            # no <form> elem
            return None
        except TypeError:
            # no "(sub)count" attrib (or non-int value)
            return None
        

    def _p(self, lu, subcount=False, smooth=False, cat_totals=False):
        """
        probility on the basis of MLE using (sub)counts
        """
        lu_count = self._get_lu_count(lu, subcount)
        
        if lu_count is None:
            return None
        
        # probability with optional smoothing by add-one
        if lu_count == 0 and smooth:
            lu_count = 1
            
        # optionally use the category-specific totals
        if cat_totals:
            # silently back-off to "all" if no cat was found
            cat = self._get_lu_cat(lu) or "all"
        else:
            cat = "all"
            
        count_total = float(self._cat2counts[cat])
            
        return lu_count / float(count_total)

           
    def _IC(self, lu, subcount=False, smooth=False, cat_totals=False, base=2):
        """
        Information Content
        """
        try:
            return -log(self._p(lu, subcount, smooth, cat_totals), base)
        except OverflowError:
            # zero probability: log(0) not defined
            return None
        except TypeError:
            # _prob returned None because no count was found 
            return None
        
        
    

# Debugging code

# Parsing cdb takes a long time. Therefore debugging is much faster if we
# parse just once, like this:start_server
#
# >>> import cornetto.simcornet as cornet; cornet._parse()
#    
# While debugging we inject the tables and graph in a Cornet instance:
# 
# >>> reload(cornet); c = cornet._get_cornet_instance()
#
    
#def _parse(cdb_lu="cdb_lu_minimal_subcounts.xml", cdb_syn="cdb_syn_minimal.xml"):
    #global form2lu, c_lu_id2lu, c_sy_id2synset, graph, cat2counts
    #form2lu, c_lu_id2lu, c_sy_id2synset, graph, cat2counts = \
    #parse_cdb_with_counts(cdb_lu, cdb_syn, verbose=False)
    

#def _get_cornet_instance():
    #c = SimCornet()
    #c._form2lu = form2lu
    #c._c_lu_id2lu = c_lu_id2lu
    #c._c_sy_id2synset =  c_sy_id2synset
    #c._graph = graph
    #c._cat2counts = cat2counts
    #return c

