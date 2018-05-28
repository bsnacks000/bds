from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *

""" general purpose functionality. Classes are loosely classified by method type
"""

import datetime
from dateutil.relativedelta import relativedelta
import os
import pandas as pd
import numpy as np

import logging
l = logging.getLogger(__name__)


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
