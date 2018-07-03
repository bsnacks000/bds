""" tests for the utils module
"""

import unittest 
from binx.utils import bfs_shortest_path, ObjUtils, RecordUtils, DataFrameDtypeConversion 

import pandas as pd
from pandas.testing import assert_frame_equal
import numpy as np 


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