===
bds
===


.. image:: https://img.shields.io/pypi/v/bds.svg
        :target: https://pypi.python.org/pypi/bds

.. image:: https://img.shields.io/travis/bsnacks000/bds.svg
        :target: https://travis-ci.org/bsnacks000/bds

.. image:: https://readthedocs.org/projects/bds/badge/?version=latest
        :target: https://bds.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

:version: 0.1.1


Interfaces for an in-memory datastore and calc framework using marshmallow + pandas


* Free software: MIT license
* Documentation: https://bds.readthedocs.io.


Features
--------

This set of interfaces are designed to help you take your data science project/notebook
and easily turn it into a serializable web-ready API without having to depend on a specific
application or web-framework.

This can help you quickly scale up your scripts and create uniformity between your projects!

bds provides:

* A declarative style in memory datastore (collections)
* interfaces and base classes for processing and scaling up your calc scripts (calc, factory)
* consistent API for moving your data between json, py-objs, and pandas dataframes

Coming Soon
-----------

* A generative orm-style query/filter API for collections based on pandas
* ability to set unique constraints on collection objects
