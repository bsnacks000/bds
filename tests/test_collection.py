from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import unittest
import os

from binx.collection import InternalObject, BaseSerializer, BaseCollection
from binx.exceptions import InternalNotDefinedError, CollectionLoadError

import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal, assert_series_equal
from marshmallow import fields
from marshmallow.exceptions import ValidationError

from pprint import pprint


class InternalSerializer(BaseSerializer):
    #NOTE used in the test below
    bdbid = fields.Integer()
    name = fields.Str()

class InternalDtypeTestSerializer(BaseSerializer):
    # tests that dtypes are being interpretted correctly in collection.to_dataframe
    id = fields.Integer(allow_none=True)
    name = fields.Str(allow_none=True)
    number = fields.Float(allow_none=True)
    date = fields.Date('%Y-%m-%d', allow_none=True)
    datet = fields.DateTime('%Y-%m-%d %H:%M:%S', allow_none=True)
    tf = fields.Bool(allow_none=True)
    some_list = fields.List(fields.Integer, allow_none=True)


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

    def test_serializer_get_numpy_dtypes(self):

        s = InternalSerializer(internal=InternalObject, strict=True)
        data = [{'bdbid': 1, 'name': 'hi-there'}, {'bdbid': 2, 'name': 'hi-ho'}]
        obj, _ = s.load(data, many=True)

        out = s.get_numpy_fields()
        self.assertEqual(out['bdbid'], np.dtype('int64'))
        self.assertEqual(out['name'], np.dtype('<U'))

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

        self.dtype_test_data = [
            {'id': 1, 'name': 'hep', 'number': 42.666, 'date': '2017-05-04', 'datet': '2017-05-04 10:30:24', 'tf':True, 'some_list':[1,2,3]},
            {'id': 2, 'name': 'xup', 'number': 41.666, 'date': '2016-05-04', 'datet': '2016-05-04 10:30:24', 'tf':False, 'some_list':[4,5,6]},
            {'id': 3, 'name': 'pup', 'number': 40.666, 'date': '2015-05-04', 'datet': '2015-05-04 10:30:24', 'tf':True, 'some_list':[7,8,9]},
        ]

        self.dtype_test_data_none = [
            {'id': 1, 'name': 'hep', 'number': 42.666, 'date': '2017-05-04', 'datet': '2017-05-04 10:30:24', 'tf':True, 'some_list':None},
            {'id': 2, 'name': None, 'number': 41.666, 'date': '2016-05-04', 'datet': None, 'tf':False, 'some_list':[4,5,6]},
            {'id': 3, 'name': 'pup', 'number': None, 'date': '2015-05-04', 'datet': '2015-05-04 10:30:24', 'tf':True, 'some_list':[7,8,9]},

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

        base.load_data(df)

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


    def test_base_collection_dataframe_with_dtypes(self):

        BaseCollection.serializer_class = InternalDtypeTestSerializer # NOTE patching a different serializer here
        base = BaseCollection()
        base.load_data(self.dtype_test_data)

        df = base.to_dataframe()
        correct_dtypes = pd.Series([
            np.dtype('int64'), np.dtype('object'), np.dtype('float64'),
            np.dtype('datetime64[ns]'),np.dtype('datetime64[ns]'),np.dtype('bool'),
            np.dtype('object')
            ], index=['id', 'name', 'number', 'date', 'datet', 'tf', 'some_list'])

        assert_series_equal(df.dtypes, correct_dtypes)

        base2 = BaseCollection()
        base2.load_data(self.dtype_test_data_none)
        df = base2.to_dataframe()

        self.assertTrue(df.isnull().values.any())

        BaseCollection.serializer_class = InternalSerializer #NOTE must patch this back here


    def test_new_collection_instances_register_on_serializer_and_internal(self):

        base = BaseCollection()

        test = BaseCollection in base.serializer.registered_colls
        self.assertTrue(test)

        BaseCollection in base.internal.registered_colls
        self.assertTrue(test)
