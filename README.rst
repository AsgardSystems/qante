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

| We invite you to view a `YouTube Video`_ of our `talk`_ on `PyData Global 2022`_:
|  ∙ `pydataG22.pdf`_ contains slides of our talk.
|  ∙ `ipynb/pydata.ipynb`_ contains a ``jupyter notebook`` with examples.

| Use pip or python (rev 3 or above) to install from `PyPI`_:
|  ``pip install qante`` (or ``python -m pip install qante``)

Use python docstrings for API Documentation::

  python    # rev 3 or above
    from quante.tagger import Tagger
    from quante.query import Query
    from quante import loctuple as lt
    from quant.table import get_table

    help(Tagger)    # annotate text with tags using tagRE('tagname', regexp)
    help(Query)     # Syntax for querying annotated text
    help(lt)        # Predicates used by queries
    help(get_table) # extract table (as dictionaries) from text


See also: "API Documentation" at the end of our jupyter notebook.


We welcome your questions by electronic mail at: qante{at}asgard.com


.. _`PyPI`: https://pypi.org
.. _`talk`: https://global2022.pydata.org/cfp/talk/LUYPAE/
.. _`PyData Global 2022`: https://pydata.org/global2022/
.. _`YouTube Video`: https://www.youtube.com/watch?v=gVqshlX4aW0&t=37949s
.. _`pydataG22.pdf`: https://github.com/AsgardSystems/qante/blob/main/pydataG22.pdf
.. _`ipynb/pydata.ipynb`:  https://github.com/AsgardSystems/qante/blob/main/ipynb/pydata.ipynb
