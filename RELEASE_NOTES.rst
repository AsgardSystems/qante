Qante Release Notes
===================

0.0.5 - Aug 2023
----------------

This release improves the performance of the query engine. 
It now estimates the computation time of two alternatives to evaluate a predicate 
and selects the one with the shortest time. The alternatives are:

1. expand previous results to include tags in the predicate and apply predicate to the expansion
2. evaluate the predicate on its tags and then join the result with the previous result

Also, these bugs were fixed:

1. handles empty tables in function to extract tables: returns []
2. handles character '|' in literal
3. fix regular expressions for lines and words

The following source files were updated:

loctuple.py:

* added comments
* added function intersection(pair): returns location of intersection of pair[0] and pair[1]

| query.py: optimized query engine
| table.py: return [] if table is empty
| tagger.py: handle character ‘|’ in literal
| utilities.py: fixed regular expressions for lines and words


0.0.4 - Dec 2022 
----------------

Initial Release for PyData Global 2022.
