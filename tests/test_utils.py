""" tests for the utils module
"""

import unittest
from binx.utils import bfs_shortest_path, ObjUtils, RecordUtils, DataFrameDtypeConversion

import pandas as pd
from pandas.testing import assert_frame_equal
import numpy as np
from marshmallow import fields

from datetime import datetime, date

class TestUtils(unittest.TestCase):

    def setUp(self):
        self.objutils = ObjUtils()
        self.recordutils = RecordUtils()
        self.dfconv = DataFrameDtypeConversion()

    def test_record_utils_replace_nan_with_none(self):
        records = [
            {'a': 1,'b':2},
            {'a': np.nan,'b':3},
            {'a': 4,'b': np.nan}
        ]
        test = [
            {'a': 1,'b':2},
            {'a': None,'b':3},
            {'a': 4,'b': None}
        ]
        r = self.recordutils.replace_nan_with_none(records)
        self.assertEqual(r, test)



    def test_record_utils_columns_to_records(self):
        cols = {'a': [1,2], 'b': [3,4]}
        test = [
            {'a':1, 'b':3},
            {'a':2, 'b':4}
        ]
        r = self.recordutils.columns_to_records(cols)
        self.assertEqual(test, r)

    def test_record_utils_records_to_columns(self):
        records = [
            {'a':1, 'b':3},
            {'a':2, 'b':4}
        ]
        test = {'a': [1,2], 'b': [3,4]}
        c = self.recordutils.records_to_columns(records)
        self.assertEqual(test, c)


    def test_obj_util_get_fully_qualified_path(self):
        class Test:
            pass
        t = Test()
        clspath = self.objutils.get_fully_qualified_path(t)
        self.assertEqual('tests.test_utils.Test', clspath)


    def test_dfconv_df_nan_to_none(self):
        df = pd.DataFrame({'a':[1, np.nan], 'b':[2,np.nan]})
        test = pd.DataFrame({'a':[1, None], 'b':[2,None]})

        d = self.dfconv.df_nan_to_none(df)
        assert_frame_equal(d, test, check_dtype=False)


    def test_dfconv_df_none_to_nan(self):
        df = pd.DataFrame({'a':[1, None], 'b':[2,None]})
        test = pd.DataFrame({'a':[1, np.nan], 'b':[2,np.nan]})

        d = self.dfconv.df_none_to_nan(df)
        assert_frame_equal(test, d)


    def test_bfs_shortest_path(self):

        graph = {
            'A': set(['B', 'C']),
            'B': set(['A', 'D', 'E']),
            'C': set(['A', 'F']),
            'D': set(['B']),
            'E': set(['B', 'F']),
            'F': set(['C', 'E'])
        }
        test = ['A', 'C', 'F']
        result = bfs_shortest_path(graph, 'A', 'F')
        self.assertEqual(test, result)

        test = ['A', 'B', 'D']
        result = bfs_shortest_path(graph, 'A', 'D')
        self.assertEqual(result, test)


    def test_dfconv_date_to_string(self):

        # note that only datetime objects get converted to pd.Timestamps.
        # datetime.date objects are loaded in as type object not type pd.TimeStamp
        records = [
            {'a': 1, 'b': datetime(2017,5,4, 10, 10, 10), 'c': datetime(2017,5,4)},
            {'a': 2, 'b': datetime(2017,6,4, 10, 10, 10), 'c': datetime(2018,5,4)},
            {'a': 3, 'b': datetime(2017,7,4, 10, 10, 10), 'c': datetime(2019,5,4)},
        ]
        col_mapping = {'b': '%Y-%m-%d %H:%M:%S', 'c': '%Y-%m-%d'}

        df = pd.DataFrame.from_records(records)
        test_recs = self.dfconv.date_to_string(col_mapping, df)

        self.assertEqual(str(test_recs['b'].dtype), 'object')
        self.assertEqual(str(test_recs['c'].dtype), 'object')

    def test_record_util_date_to_string(self):

        records = [
            {'a': 1, 'b': datetime(2017,5,4, 10, 10, 10), 'c': date(2017,5,4)},
        ]

        col_mapping = {'b': '%Y-%m-%d %H:%M:%S', 'c': '%Y-%m-%d'}
        test = [{'a': 1, 'b': '2017-05-04 10:10:10', 'c': '2017-05-04'}]

        test_recs = self.recordutils.date_to_string(col_mapping, records)

        self.assertListEqual(test, test_recs)
    
    def test_record_util_date_to_string_with_numpy_and_pandas(self):
        records = [
            {'a': 1, 'b': pd.Timestamp(2017,5,4, 10, 10, 10), 'c': np.datetime64('2017-05-04')},
        ]

        col_mapping = {'b': '%Y-%m-%d %H:%M:%S', 'c': '%Y-%m-%d'}
        test = [{'a': 1, 'b': '2017-05-04 10:10:10', 'c': '2017-05-04'}]

        test_recs = self.recordutils.date_to_string(col_mapping, records)

        self.assertListEqual(test, test_recs)
    


