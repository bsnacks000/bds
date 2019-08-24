import unittest
import os

from binx.collection import InternalObject, BaseSerializer, BaseCollection
from binx.exceptions import InternalNotDefinedError, CollectionLoadError, CollectionValidationError

import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal, assert_series_equal
from marshmallow import fields, INCLUDE, EXCLUDE
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
    date = fields.Date( allow_none=True)
    datet = fields.DateTime(allow_none=True)
    tf = fields.Bool(allow_none=True)
    some_list = fields.List(fields.Integer, allow_none=True)

    class Meta:
        dateformat = '%Y-%m-%d'
        datetimeformat = '%Y-%m-%d %H:%M:%S'

class DateStringFormatTestSerializer(BaseSerializer):
    a = fields.Integer()
    b = fields.DateTime()
    c = fields.Date()

    class Meta:
        dateformat = '%Y-%m-%d'
        datetimeformat = '%Y-%m-%d %H:%M:%S'



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
        s = InternalSerializer(internal=InternalObject)
        self.assertTrue(hasattr(s, '_InternalClass'))


    def test_internal_class_kwarg_raises_InternalNotDefinedError(self):

        with self.assertRaises(InternalNotDefinedError):
            s = InternalSerializer()


    def test_serializer_post_load_hook_returns_internal_class(self):

        s = InternalSerializer(internal=InternalObject)
        data = [{'bdbid': 1, 'name': 'hi-there'}, {'bdbid': 2, 'name': 'hi-ho'}]
        obj = s.load(data, many=True)
        for i in obj:
            self.assertIsInstance(i, InternalObject)

    def test_serializer_get_numpy_dtypes(self):

        s = InternalSerializer(internal=InternalObject)
        data = [{'bdbid': 1, 'name': 'hi-there'}, {'bdbid': 2, 'name': 'hi-ho'}]
        obj = s.load(data, many=True)

        out = s.get_numpy_fields()
        self.assertEqual(out['bdbid'], np.dtype('int64'))
        self.assertEqual(out['name'], np.dtype('<U'))


    def test_serializer_dateformat_fields(self):

        s = DateStringFormatTestSerializer(internal=InternalObject)
        test = {'b': '%Y-%m-%d %H:%M:%S', 'c': '%Y-%m-%d'}
        self.assertDictEqual(test, s.dateformat_fields)


    def test_extra_fields_raise_error(self):
        # this is specific to ma 3
        class ExtraFieldTestSerializer(BaseSerializer):
            id = fields.Integer()
            name = fields.Str()

        data = [
            {'id': 1, 'name': 'hep'},
            {'id': 2, 'name': 'tups', 'what': 'is this'}
        ]

        s = ExtraFieldTestSerializer(internal=InternalObject)

        with self.assertRaises(ValidationError):
            s.load(data, many=True)


    def test_required_true_expected_behavior(self):
        # making sure this didn't change in ma3
        class RequiredTrueTestSerializer(BaseSerializer):
            id = fields.Integer(required=True)
            name = fields.Str(required=False)
            blah = fields.Str(required=False)


        data = [
            {'id': 1},
            {'id': 2}
        ]
        s = RequiredTrueTestSerializer(internal=InternalObject)
        works = s.load(data, many=True)
        for w in works:
            self.assertIsInstance(w, InternalObject)

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

        self.dtyp_test_data_all_none = [
            {'id': None, 'name': None, 'number': None, 'date': None, 'datet': '2017-05-04 10:30:24', 'tf':True, 'some_list':None},
            {'id': None, 'name': None, 'number': None, 'date': None, 'datet': None, 'tf':False, 'some_list':[4,5,6]},
            {'id': None, 'name': None, 'number': None, 'date': None, 'datet': '2015-05-04 10:30:24', 'tf':True, 'some_list':[7,8,9]},
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


    def test_subclass_collection_concatentaion_throws_TypeError_on_wrong_type(self):

        class TestSerializer(BaseSerializer):
            bdbid = fields.Integer()
            name = fields.String()

        class DummyCollectionA(BaseCollection):
            serializer_class = TestSerializer
            internal_class = InternalObject

        class DummyCollectionB(BaseCollection):
            serializer_class = TestSerializer
            internal_class = InternalObject

        d = DummyCollectionA()
        d.load_data(self.data)

        e = DummyCollectionB()
        e.load_data(self.data)

        with self.assertRaises(TypeError):
            new_base = e + d


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


    def test_non_required_int_fields_do_not_raise_TypeError_in_to_dataframe(self):

        class TestIntSerializer(BaseSerializer):
            test_id = fields.Integer(allow_none=True)

        BaseCollection.serializer_class = TestIntSerializer  # these fields are not required

        records = [{'test_id': None}, {'test_id': 2}]
        #expected_result = [{'test_id': np.nan}, {'test_id': 2.0}]
        b = BaseCollection()
        b.load_data(records)
        df = b.to_dataframe()
        check = df.to_dict('records')

        self.assertTrue(np.isnan(check[0]['test_id'])) #NOTE coerced to nan and float
        self.assertEqual(check[1]['test_id'], 2.0)


    def test_non_required_date_fields_do_not_raiseTypeError_in_to_dataframe(self):
        class TestDateSerializer(BaseSerializer):
            test_date = fields.Date('%Y-%m-%d',  allow_none=True)

        BaseCollection.serializer_class = TestDateSerializer  # these fields are not required

        records = [{'test_date': None}, {'test_date': '2017-07-01'}]
        b = BaseCollection()
        b.load_data(records)
        df = b.to_dataframe()
        check = df.to_dict('records')
        self.assertEqual(str(check[0]['test_date']), 'NaT')
        self.assertEqual(pd.Timestamp('2017-07-01'), check[1]['test_date'])


    def test_empty_collection_returns_empty_dataframe_in_to_dataframe(self):

        BaseCollection.serializer_class = InternalSerializer
        records = []

        b = BaseCollection()
        b.load_data(records)

        df = b.to_dataframe()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)


    def test_empty_collection_raises_CollectionLoadError_if_passed_empty_record_collection(self):

        BaseCollection.serializer_class = InternalSerializer
        records = []

        b = BaseCollection()
        with self.assertRaises(CollectionLoadError):
            b.load_data(records, raise_on_empty=True)


    def test_None_to_nan_conversion_all_none(self):
        BaseCollection.serializer_class = InternalDtypeTestSerializer

        b = BaseCollection()
        b.load_data(self.dtyp_test_data_all_none)
        df = b.to_dataframe() # would raise here
        self.assertIsInstance(df, pd.DataFrame)


    def test_data_load_via_init_works_as_expected(self):

        class TestInitSerializer(BaseSerializer):
            id = fields.Integer(required=True)
            name = fields.String()
            mydate = fields.Date()

            class Meta:
                dateformat = '%Y-%m-%d'


        BaseCollection.serializer_class = TestInitSerializer

        data = [
            {'id': 1, 'name': 'hep'},
            {'id': 2, 'name': 'tups','mydate': '2017-07-01'}
        ]

        coll = BaseCollection(data)

        for c in coll:
            self.assertIsInstance(c, InternalObject)


    def test_data_load_raises_validation_error(self):

        class TestDataLoadSerializer(BaseSerializer):
            id = fields.Integer(required=True)
            name = fields.String()
            mydate = fields.Date()

            class Meta:
                dateformat = '%Y-%m-%d'


        BaseCollection.serializer_class = TestDataLoadSerializer

        data = [
            {'id': 1, 'name': 'hep'},
            {'bad': 'idea'}
        ]

        with self.assertRaises(ValidationError):
            coll = BaseCollection(data)



    def test_ma_kwargs_in_constructor_pass_to_serializer(self):

        class TestMaKwargsSerializer(BaseSerializer):
            id = fields.Integer(required=True)
            name = fields.String()
            mydate = fields.Date()

            class Meta:
                dateformat = '%Y-%m-%d'


        BaseCollection.serializer_class = TestMaKwargsSerializer

        data = [
            {'id': 1, 'name': 'hep'},
            {'id': 2, 'name': 'tups','mydate': '2017-07-01', 'random': 'thing'},
            {'id': 3, 'who': 'am i'} # test ma3 unknown=INCLUDE
        ]

        coll = BaseCollection(data, unknown=EXCLUDE)
        expected = [{'id': 1, 'name': 'hep'},
            {'id': 2, 'mydate': '2017-07-01', 'name': 'tups'},
            {'id': 3}]

        self.assertListEqual(coll.data, expected)

        coll2 = BaseCollection(data, unknown=INCLUDE, only=['id', 'name'])
        expected = [{'id': 1, 'name': 'hep'}, {'id': 2, 'name': 'tups'}, {'id': 3}]

        self.assertListEqual(coll2.data, expected)


