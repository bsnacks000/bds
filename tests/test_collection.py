from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import unittest
import os

from binx.collection import InternalObject, BaseSerializer, BaseCollection
from binx.exceptions import InternalNotDefinedError, CollectionLoadError

import pandas as pd
from pandas.testing import assert_frame_equal
from marshmallow import fields
from marshmallow.exceptions import ValidationError

from pprint import pprint


class InternalSerializer(BaseSerializer):
    #NOTE used in the test below
    bdbid = fields.Integer()
    name = fields.Str()


class TestInternalObject(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.obj = InternalObject(bdbid=1, name='hi')


    def setUp(self):
        self.obj = self.__class__.obj


    def test_internal_object_updates_kwargs(self):
        self.assertTrue(hasattr(self.obj, 'bdbid'))
        self.assertTrue(hasattr(self.obj, 'name'))




class TestBaseSerializer(unittest.TestCase):

    def test_internal_class_kwarg(self):
        s = InternalSerializer(internal=InternalObject, strict=True)
        self.assertTrue(hasattr(s, '_InternalClass'))


    def test_internal_class_kwarg_raises_InternalNotDefinedError(self):

        with self.assertRaises(InternalNotDefinedError):
            s = InternalSerializer()


    def test_serializer_post_load_hook_returns_internal_class(self):

        s = InternalSerializer(internal=InternalObject, strict=True)
        data = [{'bdbid': 1, 'name': 'hi-there'}, {'bdbid': 2, 'name': 'hi-ho'}]
        obj, _ = s.load(data, many=True)
        for i in obj:
            self.assertIsInstance(i, InternalObject)



class TestBaseCollection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #NOTE monkey patch the class
        BaseCollection.serializer_class = InternalSerializer
        BaseCollection.internal_class = InternalObject

    def setUp(self):
        #tests the load method
        self.data = [
            {'bdbid': 1, 'name': 'hi-there'},
            {'bdbid': 2, 'name': 'hi-ho'},
            {'bdbid': 3, 'name': 'whoop'},
        ]

        self.data_with_none = [
            {'name': 1, 'name': 'hi-there'},
            {'bdbid': 2, 'name': 'hi-ho'},
            {'bdbid': None, 'name': 'whoop'},
        ]

        self.data_with_missing_field = [
            {'name': 1 },
            {'bdbid': 2 },
            {'bdbid': 3, 'name': 'whoop'},
        ]

        self.data_bad_input = [
            {'bdbid': 'hep', 'name': 'hi-there'},
            {'bdbid': 2, 'name': 'hi-ho'},
            {'bdbid': 3, 'name': 'whoop'},
        ]


    def test_base_collection_correctly_loads_good_data(self):
        base = BaseCollection()
        base.load_data(self.data)

        for i in base._data: # creates InternalObject Instances
            self.assertIsInstance(i, InternalObject)


    def test_base_collection_raises_CollectionLoadError(self):
        base = BaseCollection()

        base._serializer = None  # patching to None
        with self.assertRaises(CollectionLoadError):
            base.load_data(self.data)


    def test_base_collection_rasies_ValidationError(self):

        base = BaseCollection()

        # test 3 cases where data is bad
        with self.assertRaises(ValidationError):
            base.load_data(self.data_with_none)

        with self.assertRaises(ValidationError):
            base.load_data(self.data_with_missing_field)

        with self.assertRaises(ValidationError):
            base.load_data(self.data_bad_input)


    def test_load_data_from_dataframe(self):

        df = pd.DataFrame(self.data)
        base = BaseCollection()

        base.load_data(df, from_df=True)

        for i in base._data:
            self.assertIsInstance(i, InternalObject)



    def test_base_collection_is_iterable(self):

        base = BaseCollection()
        base.load_data(self.data)

        for i in self.data: # loop over data objects
            self.assertIsInstance(i, dict)  # returns


    def test_base_collection_returns_len(self):
        base = BaseCollection()
        base.load_data(self.data)

        self.assertEqual(len(base), len(self.data))



    def test_base_collection_concatenation(self):

        base = BaseCollection()
        base.load_data(self.data)

        base2 = BaseCollection()
        base2.load_data(self.data)

        new_base = base + base2

    def test_base_collection_to_dataframe(self):

        base = BaseCollection()
        base.load_data(self.data)

        test = base.to_dataframe()

        assert_frame_equal(test, pd.DataFrame(self.data))
