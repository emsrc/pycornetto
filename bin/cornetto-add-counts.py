#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
add word counts to Cornetto lexical units database file

The word count file should have three columns, delimited by white space,
containing (1) the count, (2) the lemma, (3) the main POS tag.
The tagset is assumed to be the Spoken Dutch Corpus tagset,
and the character encoding must be ISO-8859-1.

The counts appear as the value of the feature "count" on <form> elements.
The updated lexical units xml database is written to standard output.

Since we have only the lemma and the POS, and no word sense, the frequency
information is added to each matching lexical unit regardless of its sense
(i.e. the value of the "c_seq_nr" attribute).
"""

# TODO:
# - deal with multiword counts


__author__ = 'Erwin Marsi <e.marsi@gmail.com>'
__version__ = '0.6'

from sys import stderr, stdout
from xml.etree.cElementTree import iterparse, SubElement, tostring, ElementTree

from cornetto.argparse import ArgumentParser, RawDescriptionHelpFormatter


def read_counts(file):
    if not hasattr(file, "read"):
        file = open(file)
        
    counts = {}
    totals = dict(noun=0, verb=0, adj=0, other=0)
    
    for l in file:
        try:
            count, form, tag = l.strip().split()
        except ValueError:
            stderr.write("Warning; ill-formed line: %s\n" % repr(l))
            continue
        
        # translate CGN tagset to word category
        if tag in ("N", "VNW", "TW", "SPEC"):
            cat = "noun"
        elif tag in ("WW"):
            cat = "verb"
        elif tag in ("ADJ", "BW"):
            cat = "adj"
        else:
            # LET LID TSW VG VZ
            cat = "other"
            
        # Cornetto word forms are stored in unicode
        form = form.decode("iso-8859-1")
        count = int(count)
        
        if form not in counts:
            counts[form] = dict(noun=0, verb=0, adj=0, other=0)
        
        counts[form][cat] += count
        totals[cat] += count
        
    return counts, totals



def add_count_attrib(counts, totals, cdb_lu_file):
    parser = iterparse(cdb_lu_file)
    
    for event, elem in parser:
        if elem.tag == "form":
            # following the ElementTree conventions, 
            # word form will be ascii or unicode
            form = elem.get("form-spelling")
            # lower case because Cornette is not consistent
            cat = elem.get("form-cat").lower()
            
            # fix category flaws in current release of Cornetto
            if cat == "adjective":
                cat = "adj"
            elif cat == "adverb":
                cat = "other"
            
            try:
                count = counts[form][cat]
            except KeyError:
                # form not found
                count = 0

            elem.set("count", str(count))
            
    # Finally, add totals, per category and overall,  to the doc root
    # Note that all words _not_ in Cornetto are not included in these totals 
    totals["all"] = sum(totals.values())
    
    for cat, count in totals.items():
        parser.root.set("count-total-%s" % cat, str(count))
        
    return ElementTree(parser.root)


parser = ArgumentParser(description=__doc__,
                        version="%(prog)s version " + __version__,
                        formatter_class=RawDescriptionHelpFormatter)

parser.add_argument("cdb_lu", type=file,
                    help="xml file containing the lexical units")

parser.add_argument("word_counts", type=file,
                    help="tabular file containing the word counts")

args = parser.parse_args()


counts, totals = read_counts(args.word_counts)

etree = add_count_attrib(counts, totals, args.cdb_lu)
    
etree.write(stdout, encoding="utf-8")


#def add_statistics_elem(counts, cdb_lu_file):

    #"""
    #adds a separate <statistics> element, 
    #which accomodates for other counts for other sources
    #"""
    #parser = iterparse(cdb_lu_file)
    
    #for event, elem in parser:
        #if elem.tag == "cdb_lu":
            #try:
                #count = counts[form][cat]
            #except KeyError:
                #count = 0
            
            #freq_el = SubElement(elem, "statistics")
            #SubElement(freq_el, "count", scr="uvt").text = str(count)
            
        #elif elem.tag == "form":
            ## following the ElementTree conventions, 
            ## word form will be ascii or unicode
            #form = elem.get("form-spelling")
            #cat = elem.get("form-cat")
            
    #return ElementTree(parser.root)
