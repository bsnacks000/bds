""" These are basic integration tests for the adapter class
"""

import unittest
import os

from binx.collection import BaseCollection, BaseSerializer, CollectionBuilder
from binx.adapter import AdapterOutputContainer, AbstractAdapter, register_adapter
from marshmallow import fields

class TestASerializer(BaseSerializer):
    a = fields.Integer()


class TestBSerializer(BaseSerializer):
    a = fields.Integer()
    b = fields.Integer()

class TestCSerializer(BaseSerializer):
    a = fields.Integer()
    b = fields.Integer()
    c = fields.Integer()


class TestAdapterOutputContainer(unittest.TestCase):

    def setUp(self):

        builder = CollectionBuilder('TestOutput')
        self.TestOutputCollection = builder.build(TestASerializer)  #NOTE integrated with builder here

        self.test_a = self.TestOutputCollection()
        self.test_a.load_data([{'a': 1}, {'a': 2}, {'a': 3}])


    def test_adapter_output_container(self):

        # check that it loads both a container and a context kwargs
        adapter_out = AdapterOutputContainer(self.test_a, hep='tup', zup='pup')

        #print(self.test_a.__class__.__name__)

        check_context = {'hep': 'tup', 'zup': 'pup'}
        check_obj_vars = vars(adapter_out)

        self.assertEqual(check_context, adapter_out.context)
        self.assertIsInstance(adapter_out.collection, self.TestOutputCollection)


class TestSimpleAdapter(unittest.TestCase):
    #NOTE isolated tests for simple adaptation

    @classmethod
    def setUpClass(cls):
        builder = CollectionBuilder('TestA')
        cls.TestACollection = builder.build(TestASerializer)

        builder.name = 'TestB'
        cls.TestBCollection = builder.build(TestBSerializer)


        class SimpleAToBAdapter(AbstractAdapter):
            from_collection_class = cls.TestACollection
            target_collection_class = cls.TestBCollection

            def adapt(self, collection, **context):
                df = collection.to_dataframe()
                df['b'] = 42  # add a column with some dataframe here

                return self.render_return(df, context_var='hep', other_context_var='tup')

        cls.SimpleAToBAdapter = SimpleAToBAdapter
        register_adapter(cls.SimpleAToBAdapter)

    def setUp(self):
        self.SimpleAToBAdapter = self.__class__.SimpleAToBAdapter
        self.TestBCollection = self.__class__.TestBCollection
        self.TestACollection = self.__class__.TestACollection


    def tearDown(self):
        self.SimpleAToBAdapter = None
        self.TestBCollection = None
        self.TestACollection = None


    def test_adapter_is_registered_correctly(self):

        self.assertTrue(self.SimpleAToBAdapter.is_registered)

        # check that it is registered correctly... Adapter should be in the from class, from_class should be in target
        entry = self.TestACollection.get_registry_entry()
        self.assertIn(self.SimpleAToBAdapter, entry[1]['registered_adapters'])

        entry = self.TestBCollection.get_registry_entry()
        self.assertIn(self.TestACollection, entry[1]['adaptable_from'])


    def test_adapter_produces_expected_output_container(self):
        test_input_coll = self.TestACollection()
        test_input_coll.load_data([{'a': 1}, {'a': 2}, {'a': 3}])

        test_adapter = self.SimpleAToBAdapter()
        adapted = test_adapter(test_input_coll)
        self.assertIn('context_var', vars(adapted))
        self.assertIn('other_context_var', vars(adapted))

        for record in adapted.collection.data:
            self.assertIn('b',record)

    def test_adapter_call_raises_TypeError_on_bad_input(self):
        test_input_coll = self.TestBCollection()
        with self.assertRaises(TypeError):
            test_adapter = self.SimpleAToBAdapter()
            adapted = test_adapter(test_input_coll)


    def test_adapter_call_raises_TypeError_on_bad_output_class(self):
        def bogus_adapt(self, collection, **context):
            df = collection.to_dataframe()
            df['b'] = 42  # add a column with some dataframe here

            return df

        def adapt(self, collection, **context):
            df = collection.to_dataframe()
            df['b'] = 42  # add a column with some dataframe here

            return self.render_return(df, context_var='hep', other_context_var='tup')


        self.SimpleAToBAdapter.adapt = bogus_adapt
        test_input_coll = self.TestACollection()
        test_input_coll.load_data([{'a': 1}, {'a': 2}, {'a': 3}])

        with self.assertRaises(TypeError):
            test_adapter = self.SimpleAToBAdapter()
            adapted = test_adapter(test_input_coll)

        self.SimpleAToBAdapter.adapt = adapt



class TestAdapterCollectionIntegration(unittest.TestCase):
    """ This is to test Adapter classes
    """

    @classmethod
    def setUpClass(cls):

        builder = CollectionBuilder('TestA')
        cls.TestACollection = builder.build(TestASerializer)

        builder.name = 'TestB'
        cls.TestBCollection = builder.build(TestBSerializer)

        builder.name = 'TestC'
        cls.TestCCollection = builder.build(TestCSerializer)

        class SimpleAToBAdapter(AbstractAdapter):
            from_collection_class = cls.TestACollection
            target_collection_class = cls.TestBCollection

            def adapt(self, collection, **context):
                df = collection.to_dataframe()
                df['b'] = 42  # add a column with some dataframe here

                return self.render_return(df, context_var='hep', other_context_var='tup')


        class SimpleBToCAdapter(AbstractAdapter):
            from_collection_class = cls.TestACollection
            target_collection_class = cls.TestBCollection

            def adapt(self, collection, **context):
                df = collection.to_dataframe()
                df['b'] = 42  # add a column with some dataframe here

                return self.render_return(df, something_else='mups', some_thing='zups')

        cls.SimpleAToBAdapter = SimpleAToBAdapter
        register_adapter(cls.SimpleAToBAdapter)

        cls.SimpleBToCAdapter = SimpleBToCAdapter
        register_adapter(cls.SimpleBToCAdapter)


    def setUp(self):
        self.SimpleAToBAdapter = self.__class__.SimpleAToBAdapter
        self.TestBCollection = self.__class__.TestBCollection
        self.TestACollection = self.__class__.TestACollection
        self.TestCCollection = self.__class__.TestCCollection


    def tearDown(self):
        self.SimpleAToBAdapter = None
        self.TestBCollection = None
        self.TestACollection = None
        self.TestCCollection = None
