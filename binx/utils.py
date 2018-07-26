

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
import datetime

def bfs_shortest_path(graph, start, end):
    """ a generic bfs search algo
    """
    def _bfs_paths(graph, start, end):
        # bfs using a generator. should return shortest path if any for an iteration

        queue = [(start, [start])]
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


    def date_to_string(self, col_mapping, records):
        """converts datetime or date objects to strings
        """
        for rec in records:
            for col,dformat in col_mapping.items():
                try:
                    if isinstance(rec[col], datetime.datetime):
                        rec[col] = rec[col].strftime(dformat)
                    elif isinstance(rec[col], datetime.date):
                        rec[col] = rec[col].strftime(dformat)
                    elif isinstance(rec[col], np.datetime64):
                        rec[col] = str(rec[col])
                    elif isinstance(rec[col], pd.Timestamp):
                        rec[col] = rec[col].strftime(dformat)
                        
                except KeyError as err: 
                    # swallowing this will handle any non-required date fields that aren't present
                    l.warning('Date obj field {} was not available for dt-formatting'.format(col))

        return records


class DataFrameDtypeConversion(object):

    def df_nan_to_none(self, df):
        """ converts a dfs nan values to none
        """
        return df.where((pd.notnull(df)), None)


    def df_none_to_nan(self, df):
        """ converts a df none values to nan if needed
        """
        return df.fillna(value=np.nan)


    def date_to_string(self, col_mapping, df):
        """ converts columns of pd Timestamps (np.datetime64) to strings
        """
        for col,dformat in col_mapping.items():
            if str(df[col].dtype) == 'datetime64[ns]': # assure that the date column isn't already a string
                df[col] = df[col].dt.strftime(dformat)
        return df
