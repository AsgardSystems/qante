qante - Query ANnotated TExt
============================

Motivation
----------

Extracting the highly-valuable data from unstructured text often
results in hard-to-read, brittle, difficult-to-maintain code.
The problem is that using regular expressions directly embedded
in the program control flow does not provide the best level of
abstraction. We propose a query language (based on the tuple
relational calculus) that facilitates data extraction.
Developers can explicitly express their intent declaratively,
making their code much easier to write, read, and maintain.

Solution
--------

This package allows programmers to express what they are searching
for by using higher-level concepts to express their query as tags,
locations, and expressions on location relations.

The *location* of a string of characters within the document is
the interval defining its starting and ending position.

Locations are grouped into sets named by *tags*.  Tags can be
used in conjunctions and disjunctions of interval relations to
query for tuples of locations.

We invite you to view our `talk`_ on `PyData Global 2022`_.

Use pip or python (rev 3 or above) to install from `PyPI`_::

  pip install qante
  python -m pip install qante

API Documentation is available from python docstrings::

  python    # rev 3 or above
    import qante, qante.loc
    help(qante)
    help(qante.loc)


.. _`PyPI`: https://pypi.org
.. _`talk`: https://global2022.pydata.org/cfp/talk/LUYPAE/
.. _`PyData Global 2022`: https://pydata.org/global2022/
