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
socket server exposing Cornetto database extended with word similarity measures
through XML-RPC
"""

__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6.1'

from simcornet import SimCornet
from cornetto.server import CornetProxy


class SimCornetProxy(CornetProxy):
    """
    A proxy to the SimCornet class which exposes the similary functions 
    through XML-RPC. See CornetProxy
    """
    
    def __init__(self, cdb_lu, cdb_sy, verbose=False, max_depth=None,
                 cornet_class=SimCornet):
        CornetProxy.__init__(self, cdb_lu, cdb_sy, verbose=verbose,
                             max_depth=max_depth, cornet_class=cornet_class)
        
        
    def get_count(self, lu_spec, subcount=False, format=None):
        """
        get_count(LU_SPEC[, SUBCOUNT[, FORMAT]]) --> COUNTS
        
        Get (sub)counts for lexical units satisfying this specification
        
        Parameters:       
        
            LU_SPEC string: lexical unit specification
            SUBCOUNT bool: return subcounts instead of plain counts
            FORMAT string: output format ("spec" or "xml")  
            
            COUNTS struct: a mapping of lexical units to counts (possibly empty)
        
        Examples (output in Python format):
        
            $ get_counts("varen")
            {'varen:noun:1': 434,
             'varen:verb:1': 15803,
             'varen:verb:2': 15803,
             'varen:verb:3': 15803}
            
            $ get_counts("varen", True)
            {'varen:noun:1': 434,
             'varen:verb:1': 18977,
             'varen:verb:2': 62086,
             'varen:verb:3': 15803}
        """
        # counts may be None, which XML-RPC cannot handle
        return self._safe_return(
            self._cornet.get_count(lu_spec, subcount,
                                   self._safe_format(format)))
        

    def get_total_counts(self):
        """
        get_total_counts() --> COUNTS
        
        Get the total counts per category and overall
        
        Parameters:
        
            COUNTS struct: a mapping of categories to counts
        
        Remarks:
        
            The categories are "noun", "verb", "adj", "other";
            "all" represents the overall count.
                       
        Example (output in Python format):
        
            $ get_total_counts()
            {'adj': 62156445,
             'all': 518291832,
             'noun': 187143322,
             'other': 199269966,
             'verb': 69722099}
        """
        return self._safe_return(
            self._cornet._cat2counts)
    
    
    def get_probability(self, lu_spec, subcount=False, smooth=False,
                        cat_totals=False, format=None):
        """
        get_probability(LU_SPEC[, SUBCOUNT[, SMOOTH[, CAT_TOTALS[, FORMAT]]]]  
        --> PROB
        
        Get probability (p) for lexical units satisfying this specification,
        where the probability is defined as lu_count / total_count.

        Parameters:
        
            LU_SPEC string: lexical unit specification
            SUBCOUNT bool: use subcounts instead of plain counts
            SMOOTH bool: smooth counts by adding one to lexical units with a zero count
            CAT_TOTALS bool: use total count for category of lexical unit
                instead of overall total count
            FORMAT string: output format ("spec" or "xml")  
            
            PROB struct: a mapping of lexical units to probabilities 
                (possibly empty)
        
        Remarks:
        
            By default, the total count this is taken to be the sum of counts over
            all word forms in the Cornetto database. However, when comparing two
            words of the same category (nouns, verbs, adjectives) it may be more
            appropriate to take the sum over only the word forms of this category.
            This method is used if the keyword "cat_totals" is true.
        
        Examples (output in Python format):
        
            $ get_probabilities("varen")
            {'varen:noun:1': 8.3736608066013281e-07,
             'varen:verb:1': 3.0490544176663777e-05,
             'varen:verb:2': 3.0490544176663777e-05,
             'varen:verb:3': 3.0490544176663777e-05}
        """
        return self._safe_return(
            self._cornet.get_probability(lu_spec, subcount, smooth, cat_totals, 
                                         self._safe_format(format)))
        
        
    def get_info_content(self, lu_spec, subcount=False, smooth=False, cat_totals=False,
                         format=None):
        """
        get_info_content(LU_SPEC[, SUBCOUNT[, SMOOTH[, CAT_TOTALS[, FORMAT]]]]
        --> IC
        
        Get information content (IC) for lexical units satisfying this
        specification.
        
        Parameters:
        
            LU_SPEC string: lexical unit specification
            SUBCOUNT bool: use subcounts instead of plain counts
            SMOOTH bool: smooth counts by adding one to lexical units 
                with a zero count
            CAT_TOTALS bool: use total count for category of lexical unit
                instead of overall total count
            FORMAT string: output format ("spec" or "xml")  
            
            IC struct: a mapping of lexical units to information content 
                (possibly empty)
                
        Remarks:
        
            The information content defined as the negative log of the lexical
            unit's probability, i.e. -log_2(lu_count / total_count).
            
            If a lexical unit has a count of zero, the probability is zero,
            the log is undefined, and None is returned. Unless the keyword
            "smooth" is true, in which case the count is smoothed by adding
            one.
            
            If no lexical unit matches the specification, an empty mapping is
            returned.
        
        Examples (output in Python format):
        
            $ get_info_content("plant")
            {'plant:noun:1': 14.51769181264614}
            
            >>> pprint(c.get_info_content("plant", subcount=True))
            {'plant:noun:1': 10.482770362490861}
        """
        return self._safe_return(
            self._cornet.get_info_content(lu_spec, subcount, smooth, cat_totals, 
                                          self._safe_format(format)))
        
            
    def resnik_sim(self, lu_spec1, lu_spec2, smooth=False, cat_totals=False,
                   format=None):
        """
        resnik_sim(LU_SPEC1, LU_SPEC2[, SMOOTH[, CAT_TOTALS[, FORMAT]]]
         --> SIM
         
        Compute the semantic similarity as decribed in Philip Resnik's paper
        "Using Information Content to Evaluate Semantic Similarity in a
        Taxonomy" (1995). 
        
        Parameters:
        
            LU_SPEC_1 string: first lexical unit specification
            LU_SPEC_2 string: second lexical unit specification
            SMOOTH bool: smooth counts by adding one to lexical units 
                with a zero count
            CAT_TOTALS bool: use total count for category of lexical unit
                instead of overall total count
            FORMAT string: output format ("spec" or "xml")
            
            SIM float or False: similarity score greater than or equal 
                to zero, or False
                
        Remarks:
        
            Resnik's similarity is defined for a pair of concepts c1 and c2
            as:
            
                argmax [IC(c1) + IC(c2) - 2 * IC(lcs)] for all lcs in LCS(c1, c2)
            
            In other words, the maximum value of the information content over
            all least common subsumers of two concepts. An important point is
            that the counts of an LCS, as used in computing its probabilty, is
            the sum of its own count plus the counts of all concepts that it
            subsumes.
            
            As suggested by Resnik, it can be extended to _word_ similarity by
            taking the maximum over the scores for all concepts that are
            senses of the word. This means that if just two words are
            specified - without a category or sense - two sets of matching
            lexical units are retrieved. For every combination of lexical
            units from these two sets, the LCS is computed (if any), and the
            one with the maximum information content is selected.
            
            If no LCS is found, this can mean two things: 
            
                1. The two words have no LCS because they truely have 
                   nothing in common. In this case we assume the LCS is zero and 
                   therefore we return zero.
                2. The two words should have something in common, but the 
                   correct LCS is not present in the Cornetto database. 
                   However, since there is no way to know this, we consider this 
                   the same as (1), and zero is returned.
            
            There are two more marginal cases:
            
                1. No lexical units in the Cornetto database match the 
                   specifications. 
                2. All LCS have a subcount of zero, and no smoothing was applied,
                   so its IC is undefined. 
                   
            In both cases False is returned.
            
            Notice that it is difficult to compare Resnik's word similarities,
            because they depend on the subcounts. With identical words, for
            instance:
            
                resnik_sim("iets", "iets") = 1.3113543459343666 whereas
                resnik_sim("spotje", "spotje") = 25.141834494846584
        """
        return self._safe_return(
            self._cornet.resnik_sim(lu_spec1, lu_spec2,  smooth, cat_totals, 
                                    self._safe_format(format)))
    
    
    def jiang_conrath_dist(self, lu_spec1, lu_spec2, smooth=False,
                           cat_totals=False, format=None):
        """
        jiang_conrath_dist(LU_SPEC1, LU_SPEC2[, SMOOTH[, CAT_TOTALS[, FORMAT]]]
         --> DIST
         
        Compute the semantic distance as decribed in Jay Jiang & David
        Conrath's paper "Semantic Similarity Based on Corpus Statistics and
        Lexical Taxonomy" (1997). 
        
        Parameters:
        
            LU_SPEC_1 string: first lexical unit specification
            LU_SPEC_2 string: second lexical unit specification
            SMOOTH bool: smooth counts by adding one to lexical units 
                with a zero count
            CAT_TOTALS bool: use total count for category of lexical unit
                instead of overall total count
            FORMAT string: output format ("spec" or "xml")
            
            DIST float or False: distance greater than of equal to zero,
                or False
        
        Remarks:
        
            The Jiang & Conrath distance is defined for a pair of concepts c1
            and c2 as:
            
                argmin [IC(c1) + IC(c2) - 2 * IC(lcs)] 
                for all lcs in LCS(c1, c2)
            
            This is without the edge and node weighting scheme, which is not
            implemented here. The measure is extended to a _word_ distance
            measure by taking the minimum over the scores for all concepts
            (lexical units) that are senses of the word (cf. doc of
            resnik_sim).
            
            If no LCS is found, this can mean two things: 
            
                1. The two words have no LCS because they truely have nothing
                   in common. In this case we assume the LCS is zero and
                   therefore we return the minimun of IC(c1) + IC(c2).
                2. The two words should have something in common, but the
                   correct LCS is not present in the Cornetto database. 
                   However, since there is no way to know this, we consider 
                   this the same as (1), and we return the minimun of 
                   IC(c1) + IC(c2).
            
            There are three more marginal cases:
            
                1. No lexical units in the Cornetto database match the 
                   specifications.
                2. All matching lexical units have a subcount of zero,
                   and no smoothing was applied, so their IC is undefined. 
                3. All LCS have a subcount of zero, and no smoothing was 
                   applied, so its IC is undefined. This implies that 
                   all subsumed lexical units must have a subcount of zero, 
                   and therefore (2) must be the case as well.  
                   
            In all of these three cases False is returned.
        """
        return self._safe_return(
            self._cornet.jiang_conrath_dist(lu_spec1, lu_spec2,  
                                            smooth, cat_totals, 
                                            self._safe_format(format)))
        
    
    def jiang_conrath_sim(self, lu_spec1, lu_spec2, smooth=False,
                          cat_totals=False, format=None):
        """
        jiang_conrath_sim(LU_SPEC1, LU_SPEC2[, SMOOTH[, CAT_TOTALS[, FORMAT]]]
         --> SIM
         
        Returns Jiang & Conrath similarity. See jiang_conrath_dist
        
        Parameters:
        
            LU_SPEC_1 string: first lexical unit specification
            LU_SPEC_2 string: second lexical unit specification
            SMOOTH bool: smooth counts by adding one to lexical units 
                with a zero count
            CAT_TOTALS bool: use total count for category of lexical unit
                instead of overall total count
            FORMAT string: output format ("spec" or "xml")
            
            SIM float or False: similarity between zero and one included,
                or False
        
        Remarks:
        
            The Jiang & Conrath's similarity is defined as
            
                1 / (1 + jiang_conrath_dist) 
            
            If the distance is False, so is the similarity.
            
            The translation from distance to similarity is not uniform. That
            is, the space between the distances 1 and 2 and between the
            distances 2 and 3 is the same (i.e. 1), but the space between the
            corresponding similaraties, i.e. between 0.5 and 0.33 and between
            0.33 and 0.25, is not.
        """
        return self._safe_return(
            self._cornet.jiang_conrath_sim(lu_spec1, lu_spec2,  
                                           smooth, cat_totals, 
                                           self._safe_format(format))) 
    
    
    def lin_sim(self, lu_spec1, lu_spec2, smooth=False, cat_totals=False,
                format=None):
        """
        lin_sim(LU_SPEC1, LU_SPEC2[, SMOOTH[, CAT_TOTALS[, FORMAT]]]
         --> SIM
         
        Compute the semantic similarity as decribed in the paper Dekang Lin's 
        paper "An information-theoretic definition of similarity" (1998).
        
        Parameters:
        
            LU_SPEC_1 string: first lexical unit specification
            LU_SPEC_2 string: second lexical unit specification
            SMOOTH bool: smooth counts by adding one to lexical units 
                with a zero count
            CAT_TOTALS bool: use total count for category of lexical unit
                instead of overall total count
            FORMAT string: output format ("spec" or "xml")
            
            SIM float or False: similarity between zero and one included,
                or False
        
        Remarks:
        
            Lin's similarity is defined for a pair of concepts c1 and c2 as:
            
                argmax [2 * IC(lcs) / (IC(c1) + IC(c2))] 
                for all lcs in LCS(c1, c2)
            
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
                   
            In all of these three cases False is returned.
        """
        return self._safe_return(
            self._cornet.lin_sim(lu_spec1, lu_spec2,  
                                 smooth, cat_totals, 
                                 self._safe_format(format)))
    
    