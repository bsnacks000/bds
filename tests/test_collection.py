import unittest
import os

from binx.collection import InternalObject, BaseSerializer, BaseCollection
from binx.exceptions import InternalNotDefinedError, CollectionLoadError

import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal, assert_series_equal
from marshmallow import fields
from marshmallow.exceptions import ValidationError

from datetime import datetime, date
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

class DateStringFormatTestSerializer(BaseSerializer):
    a = fields.Integer()
    b = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    c = fields.Date(format='%Y-%m-%d')



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


    def test_serializer_dateformat_fields(self):

        s = DateStringFormatTestSerializer(internal=InternalObject, strict=True)
        test = {'b': '%Y-%m-%d %H:%M:%S', 'c': '%Y-%m-%d'}
        self.assertDictEqual(test, s.dateformat_fields)
    


class TestBaseCollection(unittest.TestCase):

    def setUp(self):
        #tests the load method
        BaseCollection.serializer_class = InternalSerializer
        BaseCollection.internal_class = InternalObject

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


    def test_base_collection_raises_ValidationError(self):

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

    def test_base_collection_concatenation_throws_TypeError_on_wrong_type(self):

        base = BaseCollection()
        base.load_data(self.data)

        class DummyCollection(BaseCollection):
            serializer_class = BaseSerializer
            internal_class = InternalObject

        d = DummyCollection()
        d.load_data(self.data)

        with self.assertRaises(TypeError):
            new_base = d + base


    def test_base_collection_to_dataframe(self):

        base = BaseCollection()
        base.load_data(self.data)

        test = base.to_dataframe()

        assert_frame_equal(test, pd.DataFrame().from_dict(self.data))


    def test_base_collection_dataframe_with_dtypes(self):

        BaseCollection.serializer_class = InternalDtypeTestSerializer # NOTE patching a different serializer here
        base = BaseCollection()
        base.load_data(self.dtype_test_data)

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


    def test_datetime_and_date_objects_get_correctly_parsed_by_load_data(self):
        BaseCollection.serializer_class = DateStringFormatTestSerializer

        records = [
            {'a': 1, 'b': datetime(2017,5,4, 10, 10, 10), 'c': date(2017,5,4)},
            {'a': 2, 'b': datetime(2017,6,4, 10, 10, 10), 'c': date(2018,5,4)},
            {'a': 3, 'b': datetime(2017,7,4, 10, 10, 10), 'c': date(2019,5,4)},
        ]

        b = BaseCollection()
        b.load_data(records)

        test = [
            {'a': 1, 'b': '2017-05-04 10:10:10', 'c': '2017-05-04'},
            {'a': 2, 'b': '2017-06-04 10:10:10', 'c': '2018-05-04'},
            {'a': 3, 'b': '2017-07-04 10:10:10', 'c': '2019-05-04'}]

        self.assertListEqual(test, b.data)

        # testing on a dataframe

        df = pd.DataFrame.from_records(records)
        b = BaseCollection()
        b.load_data(records)

        self.assertListEqual(b.data, test)


    def test_pandas_timestamp_correctly_parsed_by_load_data(self):

        BaseCollection.serializer_class = DateStringFormatTestSerializer

        records = [
            {'a': 1, 'b': pd.Timestamp(2017,5,4, 10, 10, 10), 'c': pd.Timestamp(2017,5,4)},
            {'a': 2, 'b': pd.Timestamp(2017,6,4, 10, 10, 10), 'c': pd.Timestamp(2018,5,4)},
            {'a': 3, 'b': pd.Timestamp(2017,7,4, 10, 10, 10), 'c': pd.Timestamp(2019,5,4)},
        ]

        b = BaseCollection()
        b.load_data(records)

        test = [
            {'a': 1, 'b': '2017-05-04 10:10:10', 'c': '2017-05-04'},
            {'a': 2, 'b': '2017-06-04 10:10:10', 'c': '2018-05-04'},
            {'a': 3, 'b': '2017-07-04 10:10:10', 'c': '2019-05-04'}]

        self.assertListEqual(test, b.data)

        # testing on a dataframe

        df = pd.DataFrame.from_records(records)
        b = BaseCollection()
        b.load_data(records)

        self.assertListEqual(b.data, test)


    def test_non_required_datetimes_not_present_do_not_raise_utils_key_error(self):

        # if a date field was not required and not provided a KeyError was being raised 
        # in RecordUtils. We swallow that error and only parse datefields that are in the 
        # loaded data 

        BaseCollection.serializer_class = DateStringFormatTestSerializer

        records = [
            {'a': 1, 'b': datetime(2017,5,4, 10, 10, 10)},
            {'a': 2, 'c': date(2018,5,4)},
            {'a': 3, 'b': datetime(2017,7,4, 10, 10, 10), 'c': date(2019,5,4)},
        ]

        b = BaseCollection()
        b.load_data(records)

        test = [
            {'a': 1, 'b': '2017-05-04 10:10:10' },
            {'a': 2, 'c': '2018-05-04'},
            {'a': 3, 'b': '2017-07-04 10:10:10', 'c': '2019-05-04'}
        ]

        self.assertListEqual(test, b.data)

    
    def test_non_required_fields_not_present_do_not_raise_key_error_in_to_dataframe(self):

        BaseCollection.serializer_class = InternalSerializer  # these fields are not required  

        records = [{'bdbid': 1}, {'bdbid': 2}]

        b = BaseCollection()
        b.load_data(records)

        df = b.to_dataframe()
        
        self.assertEqual(records, df.to_dict('records'))



