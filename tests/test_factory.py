""" tests core functionality of the modeler class.
The tests use several mock classes that are subclassed from
"""

from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import unittest
import os

from binx.collection import BaseSerializer, InternalObject, BaseCollection
from binx.calc import AbstractCalc, AbstractCalcResult
from binx.factory import BaseFactory

import pandas as pd
from pandas.testing import assert_frame_equal

from marshmallow import fields
from marshmallow.exceptions import ValidationError

#NOTE setting up some mock classes to use for the tests
class FakeInputSerializer(BaseSerializer):

    name = fields.Str()
    val1 = fields.Integer()
    val2 = fields.Integer()

class FakeOutputSerializer(BaseSerializer):

    name = fields.Str()
    result = fields.Integer()
    other_thing = fields.Str()

class FakeOutputInternal(InternalObject):

    def __init__(self, name, result, other_thing):
        self.name = name
        self.result = result
        self.other_thing = other_thing

class FakeInputInternal(InternalObject):

    def __init__(self, name, val1, val2):
        self.name = name
        self.val1 = val1
        self.val2 = val2


class FakeOutputCollection(BaseCollection):
    serializer_class = FakeOutputSerializer
    internal_class = FakeOutputInternal


class FakeInputCollection(BaseCollection):
    serializer_class = FakeInputSerializer
    internal_class = FakeInputInternal


class MockCalcResult(AbstractCalcResult):

    def __init__(self, name, result):
        self.name = name
        self.result = result

    def serialize(self):
        return vars(self)

class MockCalc(AbstractCalc):

    def __init__(self, name=''):
        self.name = name

    def __call__(self, df, idx):
        val1 = df['val1'].iloc[idx]
        val2 = df['val2'].iloc[idx]

        calc = val1 + val2
        return MockCalcResult(self.name, calc)


class MockFactory(BaseFactory):

    CalcClass = MockCalc
    OutputCollectionClass = FakeOutputCollection


    def load(self, collection):
        self.fake_collection = collection

    def _processor(self, idx=0):
        df = self.fake_collection.to_dataframe()
        result = self._calc(df, idx)
        result.other_thing = 'Some other thing'
        result = result.serialize()
        return [result]


class TestBaseFactory(unittest.TestCase):

    def setUp(self):
        records = [
            {'name': 'Hep', 'val1': 1, 'val2': 4},
            {'name': 'Tup', 'val1': 2, 'val2': 5},
            {'name': 'Pup', 'val1': 3, 'val2': 6}
        ]
        self.fake_input = FakeInputCollection()
        self.fake_input.load_data(records)

        self.mock_factory = MockFactory(name='passed_via_init')

    def tearDown(self):
        self.mock_factory = None

    def test_base_factory_store_init_variable_on_calc(self):
        self.assertEqual('passed_via_init', self.mock_factory.calc.name)


    def test_base_factory_inits_correct_set_output_collection(self):
        self.mock_factory.load(self.fake_input)
        self.assertIsInstance(self.mock_factory.output_collection, FakeOutputCollection)


    def test_create_returns_the_defined_output_collection(self):
        self.mock_factory.load(self.fake_input)
        result = self.mock_factory.create(idx=0)

        self.assertIsInstance(result, FakeOutputCollection)

    def test_base_factory_create_reset_true_returns_multiple_collections(self):
        self.mock_factory.load(self.fake_input)

        # call for each idx
        result1 = self.mock_factory.create(idx=0)
        result2 = self.mock_factory.create(idx=1)
        result3 = self.mock_factory.create(idx=2)

        self.assertEqual(result1.data[0]['result'], 5)
        self.assertEqual(result2.data[0]['result'], 7)
        self.assertEqual(result3.data[0]['result'], 9)

    def test_base_factory_create_reset_false_accumualtes_on_single_collection(self):
        self.mock_factory.load(self.fake_input)

        #no need to store result vars since they are getting accumulated on the same object
        self.mock_factory.create(idx=0, reset=False)
        self.mock_factory.create(idx=1, reset=False)
        self.mock_factory.create(idx=2, reset=False)

        out = self.mock_factory.output_collection

        self.assertEqual(len(out.data), 3)
        self.assertEqual(out.data[0]['result'], 5)
        self.assertEqual(out.data[1]['result'], 7)
        self.assertEqual(out.data[2]['result'], 9)
