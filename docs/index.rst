binx
====
.. image:: https://img.shields.io/pypi/v/binx.svg
        :target: https://pypi.python.org/pypi/binx

.. image:: https://circleci.com/gh/bsnacks000/binx.svg?style=svg
        :target: https://circleci.com/gh/bsnacks000/binx

.. image:: https://readthedocs.org/projects/binx/badge/?version=latest
        :target: https://binx.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

``binx`` is a small Python framework for application data modeling and transformation. It's API relies heavily on `marshmallow
<https://marshmallow.readthedocs.io/en/3.0/>`_ for validation, object serialization and storage. It's true purpose however is to expose an API that
allows developers to model procedural code into directed, acyclic graphs of arbitrary complexity. A user can define an application or library as a
family of ``binx.Collection`` objects (nodes) and use the ``binx.adapter`` module (edges) to create a network of data transformations while
guaranteeing data integrity along the way.

The main goal of the project is to provide a simple API for data scientists, engineers or developers who write alot of procedural code
to be able to organize their projects using a declarative style similar to how one might approach writing a web application using DRY principles.

An Overview and Example
-----------------------

Below is an abstract example highlighting the *adapter chain* approach that ``binx`` uses for data modeling. We have a project that needs to manipulate 3 different
objects that we must track. We start with defining some serializers and then build out an adapter chain to perform some super important calculations.

.. code-block:: python

    from binx.collection import BaseSerializer, CollectionBuilder

    # Define some serializers... We can think of these as the nodes of the graph...
    # These are essentially just plain marshmallow Schema's with some extra stuff baked in...
    class TestASerializer(BaseSerializer):
        a = fields.Integer()

    class TestBSerializer(BaseSerializer):
        a = fields.Integer()
        b = fields.Integer()

    class TestCSerializer(BaseSerializer):
        a = fields.Integer()
        b = fields.Integer()
        c = fields.Integer()

    # lets make some collections out of these serializers. I'll use the CollectionBuilder...
    builder = CollectionBuilder()

    TestACollection = builder.build(TestASerializer)
    TestBCollection = builder.build(TestBSerializer)
    TestCCollection = builder.build(TestCSerializer)

At this point we have 3 ``Collection`` objects registered in our graph. From here, we have an API that will do things like validation and object serialization
for free using the mighty `marshmallow <https://marshmallow.readthedocs.io/en/3.0/>`_. Unlike ORMs, data loading happens at the instance level. We can keep multiple instances
of the same collection and treat them as iterables. Data is loaded as lists of records and appended to the ``_data`` property as plain python objects.

We built this out with the data scientist in mind so we have the ability to automatically get a dataframe with correct dtype. We can also get a json string
so we can easily serialize and send over the wire or IPC for multiprocessing apps. The ``_data`` property holds python objects so sometimes we might need to write
methods that hook into those as well.

.. code-block:: python

    test_coll_a = TestACollection()  # instantiate
    test_coll_a.load_data([{'a': 41}])  # load a record

    data = test_coll_a.data # returns list of dicts [{'a': 41}]
    data = test_coll_a.to_dataframe()   # returns a pandas dataframe with correct dtypes based on the serializer fields.
    data = test_coll_a.to_json()   # return a json string.
    data = test_coll_a._data   # access the list of the underlying python objects (usually not recommended, but sometimes neccesary)

    test_coll_a2 = TestACollection() # make another A collection
    test_coll_a2.load_data([{'a': 999}]) # such important data...

    # we can concatenate to make a new A collection
    new_coll = test_coll_a + test_coll_a2
    data = new_coll.data   # returns [{'a': 41}, {'a':999}]

    # we can also loop if we want to work with the underlying python objects
    for d in new_coll:
       print(d.a)

Starting in version **0.4** one can configure the underlying serializer with marshmallow kwargs for better control. We also allow
data to be loaded directly via the constructor for convenience.

.. code-block:: python

    from marhsmallow import EXCLUDE

    class MySerializer(BaseSerializer):
        id = fields.Integer(required=True)
        name = fields.String()
        mydate = fields.Date()

        class Meta:
            dateformat = '%Y-%m-%d'

    builder = CollectionBuilder()
    MyCollection = builder.build(MySerializer)


    data = [
            {'id': 1, 'name': 'hep'},
            {'id': 2, 'name': 'tups','mydate': '2017-07-01', 'random': 'thing'},
            {'id': 3, 'who': 'am i'}
        ]

    # EXCLUDE is compatible with ma-2 behavior. bogus keys get dropped (default behavior throws a ValidationError)
    # only will only output the specified fields
    coll = BaseCollection(data, unknown=EXCLUDE, only=['id', 'name'])
    coll.data           #returns [{'id': 1, 'name': 'hep'}, {'id': 2, 'name': 'tups'}, {'id': 3}]


Ok, now in our project we need to perform several super complicated calculations. Starting with A we need to calculate B and cache it for later use before
finally calculating C. Along the way the calculations perform side_effects that require extra arguments. Some of these extra args are even dependent on the
previous results of the computation. Furthermore, some of the code relies on pandas/numpy and for some we need pure python. These situations happen often and can
hit you hard when you're trying to scale up your notebook script into a library or web app!!

This is where ``binx`` steps up to help us deal with managing our problem by providing us an easy to use API to govern the data-flow. Since the collections are simply nodes on a graph,
the calculations to get from one to another can be represented as edges. We call these ``Adapters`` since we're adapting the data from one schema to another.

The easiest way to create adapters is by subclassing ``binx.adapter.PluggableAdapter``, providing regsitered ``Collection`` classes for ``from`` and ``target`` as well as a callable that
does the actual computation or data manipulation.

.. code-block:: python

    from binx.adapter import PluggableAdapter, register_adapter


    def adapt_a_to_b(collection, **context):
        df = collection.to_dataframe()  # I need a dataframe
        df['b'] = 42  # add a column b and do the calc
        return df, {'context_var':'hep', 'other_context_var': 'tup'}   # the data plus the side effects that need to be passed out

    def adapt_b_to_c(collection, **context):
        data = collection.data # I need a list of records
        data['c'] = 43  # add a column c and do the calc.
        return data, dict(something_else='mups', some_thing='zups')


    class PluggableAToBAdapter(PluggableAdapter):
        from_collection_class = TestACollection
        target_collection_class = TestBCollection
        calc = adapt_a_to_b


    class PluggableBToCAdapter(PluggableAdapter):
        from_collection_class = TestBCollection
        target_collection_class = TestCCollection
        calc = adapt_b_to_c

    register_adapter(PluggableAToBAdapter)
    register_adapter(PluggableBToCAdapter)


There are a few caveats to using the ``adapter`` module that you might notice.

- ``PluggableAdapter.calc`` must be a callable.
- ``PluggableAdapter.calc`` must pass the exact signature `` ``
- The ``collection`` must be an instance of ``from_collection_class``.
- The function must return either a list of records or dataframe that binx will validate against ``target_collection_class``.
- The function must return a 2-tuple of the above data and a context. If the context was not used an empty dictionary can be passed out instead.

If you accidentally break one of these rules, binx will complain at runtime and break during the adapter call.

These sorts of restrictions are neccesary to assure that the recursive calls that happen in the graph are consistent, regardless of what is happening inside
a given adapter function. Note that the data in the ``context`` dict are accumulated globally over the course of the chained call and are not removed from the
chain if the user pops an argument. So if at some stage of the chain ``var = context.pop('a')`` is called on a context variable, ``a`` will still appear
at the end of the adpater call.

So that's basically it! We now have a small graph that makes the transformation ``TestACollection -> TestBCollection -> TestCCollection``. To use our chain
we only need to make one call to adapt A to C. Likewise if we only needed B from A we can simply adapt B to A since it is on the same path.

.. code-block:: python

    test_coll_c, context = TestCCollection.adapt(test_coll_a, accumulate=True, foo='bar')  # save B in context, also pass foo into context

If all went according to plan we have the C data we need. With ``accumulate=True`` we will get our B data as well in the ``context`` dict. This dict will also contain
the rest of the context data that was passed into binx, regardless of what might have been popped or manipulated along the way.
If anything went wrong inside the adapter chain a ``binx.exceptions.AdapterChainError`` is thrown which wraps the underlying exception.

Although this is a ridiculous example, hopefully it conveys how binx's graph based approach might be used to expand a simple method chain into a network graph
of dozens or even hundreds of nodes, all while allowing you to not have to worry about data integrity along the way.

Future dev...
-------------

I've been developing this library in what little free time I've had the passed year in order to help my coworkers and I solve problems for data driven projects within my organization.
It's difficult for me to consistently maintain it,  and since it has so far worked for me I haven't seen a need to change it much from its original concept. With v0.3.0+ I hope
to add some new features and plug some holes going forward.

**Some thoughts:**
 - create compatibility with existing projects that use marshmallow or one of its database extensions (i.e. marshmallow-sqlalchemy, marshmallow-mongoengine, etc. ).
 - rebuild the registry to use `networkx <https://networkx.github.io/>`_ over the DIY version I wrote.
 - create a *query* module of some kind that would allow easy filtering of collection instances using chaining syntax.
 - introduce options to provide collection objects with more data integrity (key constraints, de-duplication etc.)
 - add types from the *typing* module for the library to help document signatures.
 - better API docs :)

==^.^==


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   modules
   history

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
