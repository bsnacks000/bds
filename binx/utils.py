

""" general purpose functionality. Classes are loosely classified by method type
"""

import datetime
from dateutil.relativedelta import relativedelta
import os
import pandas as pd
import numpy as np

import logging
l = logging.getLogger(__name__)

from pprint import pprint 

def bfs_shortest_path(graph, start, end):
    """ a generic bfs search algo
    """
    def _bfs_paths(graph, start, end):
        # bfs using a generator. should return shortest path if any for an iteration
        #pprint('inside bfs: ' +  str(graph))
        queue = [(start, [start])]
        #pprint('queue: ' + str(queue))
        while queue:
            (vertex, path) = queue.pop(0)
            for next_vertex in graph[vertex] - set(path):
                if next_vertex == end:
                    yield path + [next_vertex]
                else:
                    queue.append((next_vertex, path + [next_vertex]))
    try:
        return next(_bfs_paths(graph, start, end))
    except StopIteration:
        return []


class ObjUtils(object):

    def get_fully_qualified_path(self, obj):
        """returns the fully qualified path of the class that defines this instance"""
        module = obj.__class__.__module__ # use the path name of the internal object on setUp
        clsname = obj.__class__.__name__
        full = '.'.join([module,clsname])
        return full



class RecordUtils(object):

    def replace_nan_with_none(self, records):
        """ checks a flat list of dicts for np.nan and replaces with None
        used for serialization of some result records. This is because
        marshmallow can not serialize and de-serialize in to NaN
        #NOTE this is a bit slow, should find a better way to make this conversion
        """
        for record in records:
            for k,v in record.items():
                if v is np.nan:
                    record[k] = None
        return records


    def records_to_columns(self, records):
        """ convert record format to column format
        """
        return {k: [d[k] for d in records] for k in records[0]}


    def columns_to_records(self, column_dict):
        """ convert column_dict format to record format
        """
        return [dict(zip(column_dict, d)) for d in zip(*column_dict.values())]




class DataFrameDtypeConversion(object):

    def df_nan_to_none(self, df):
        """ converts a dfs nan values to none
        """
        return df.where((pd.notnull(df)), None)


    def df_none_to_nan(self, df):
        """ converts a df none values to nan if needed
        """
        return df.fillna(value=np.nan)


    def end_date_slicer(self, df, start_slice_date, end_slice_date):
        ''' slices a bema_calc df by its end_date column
        :PARAMS: start_slice_date, end_slice_date - these should be converted to datetime
        :RETURNS: a sliced df
        '''
        date_filtered_df = df[(df['end_date'] >= start_slice_date) &
                (df['end_date'] <= end_slice_date)].reset_index(drop=True)

        return date_filtered_df

    def compare_two_dfs(self, left, right):
        """ returns sorted dicts for more granular comparison of values
        """

        left = left.to_dict(orient='list')
        right = right.to_dict(orient='list')

        left = {k:sorted(v) for k,v in left.items()}
        right = {k:sorted(v) for k,v in right.items()}

        return left, right
