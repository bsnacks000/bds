=======
History
=======

0.1.2 (2018-05-28)
------------------
* Port initial API from bema project
* Port original unittests
* change marshmallow api to 2.x


0.2.0 (2018-07-03)
------------------
* Built adapter module and related functionality
* removed calc_factory API (possibly will be re-included in a later build)
* created the CollectionBuilder class


0.2.1 (2018-07-12)
------------------
* patched issue relating to datetime/datestrings not being parsed by collections

0.2.2 (2018-07-26)
------------------
* patched issue relating to introspection of required columns (issue #7-#8)

0.2.3 (2018-10-01)
------------------
* clean up and fixes to cli

0.3.0 (2019-07-14)
------------------
Fixes some long standing issues and adds some new features.

* adapter.py - kwarg to accumulate optionally accumulate intermediate collections in adapter chain
* registry.py - A user warning is issued instead of exception if an identical class path name is overwritten
* collection.py - fixed errors related to creating dataframes from NoneType
* adapter.py - added a new base class PluggableAdapter to ease development of the adapter chain
* collection.py - CollectionBuilder.build now excepts an optional name arg. Will attempt to auto-parse name from serializer_class.
