====
binx
====


.. image:: https://img.shields.io/pypi/v/binx.svg
        :target: https://pypi.python.org/pypi/binx

.. image:: https://circleci.com/gh/bsnacks000/binx.svg?style=svg
        :target: https://circleci.com/gh/bsnacks000/binx

.. image:: https://readthedocs.org/projects/binx/badge/?version=latest
        :target: https://binx.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

:version: 0.4.2


``binx`` is a small Python framework for application data modeling and transformation. It's API relies heavily on `marshmallow
<https://marshmallow.readthedocs.io/en/3.0/>`_ for validation, object serialization and storage. It's true purpose however is to expose an API that
allows developers to model procedural code into directed, acyclic graphs of arbitrary complexity. A user can define an application or library as a
family of ``binx.Collection`` objects (nodes) and use the ``binx.adapter`` module (edges) to create a network of data transformations while
guaranteeing data integrity along the way.

The main goal of the project is to provide a simple API for data scientists, engineers or developers who write alot of procedural code
to be able to organize their projects using a declarative style similar to how one might approach writing a web application using DRY principles.


==^..^==

* Free software: MIT license
* Documentation: https://binx.readthedocs.io


Features
--------

This set of interfaces are designed to help you quickly scale up your notebooks/scripts and create uniformity between your projects!

binx provides:

* A declarative style in memory datastore (collections.py)
* A declarative ``Adapter`` API that helps model/manage relationships and data transformations between collections (adapter.py)
* consistent API for moving your data between json, py-objs, and pandas dataframes

