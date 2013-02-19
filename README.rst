ReBench - Execute and Document Benchmarks Reproducibly
======================================================

ReBench is a tool to run and document benchmarks. Currently, its focus lies on
benchmarking virtual machines, but nonetheless it can be used to benchmark all
kind of other applications/programs, too.

To facilitate the documentation of benchmarks, ReBench uses a text-based 
configuration format. The configuration files contain all aspects of the 
benchmark. They describe which binary was used, which parameters where given
to the benchmarks, and the number of iterations to be used to obtain 
statistically reliable results.

Thus, the documentation contains all benchmark-specific informations to 
reproduce a benchmark run. However, it does not capture the whole systems
information, and also does not include build settings for the binary that
is benchmarked. These informations can be included as comments, but are not
captured automatically.

The data of all benchmark runs is recorded in a data file and allows to 
continue aborted benchmark runs at a later time.

The data can be exported for instance as CSV or visualized with the help of
box plots.

Current Build Status
====================

|BuildStatus|_

.. |BuildStatus| image:: https://api.travis-ci.org/smarr/ReBench.png
.. _BuildStatus: https://travis-ci.org/smarr/ReBench

Credits
=======

Even though, we do not share code with `JavaStats`_, it was a strong inspiration for the creation of ReBench.

.. _JavaStats: http://www.elis.ugent.be/en/JavaStats

Furthermore, our thanks go to `Travis CI`_ for their services.

.. _Travis CI: http://travis-ci.org

Related Work
============

As already mentioned `JavaStats`_ was an important inspiration and also comes
with an OOPSLA paper titled `Statistically Rigorous Java Performance
Evaluation`_. When you want to benchmark complex systems like virtual machines
this is definitely one of the important papers to read.

Similar, `Caliper`_ is a framework for micro benchmarks and also discusses
important pitfalls not only for `Microbenchmarks`_.

.. _Statistically Rigorous Java Performance Evaluation: http://itkovian.net/base/files/papers/oopsla2007-georges-preprint.pdf
.. _Caliper: http://code.google.com/p/caliper/
.. _Microbenchmarks: http://code.google.com/p/caliper/wiki/JavaMicrobenchmarks


::

    @article{1297033,
        author = {Andy Georges and Dries Buytaert and Lieven Eeckhout},
        title = {Statistically rigorous java performance evaluation},
        journal = {SIGPLAN Not.},
        volume = {42},
        number = {10},
        year = {2007},
        issn = {0362-1340},
        pages = {57--76},
        doi = {http://doi.acm.org/10.1145/1297105.1297033},
        publisher = {ACM},
        address = {New York, NY, USA},
    }
