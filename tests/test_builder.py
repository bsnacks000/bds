
from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import unittest
import os

from binx.collection import InternalObject, BaseSerializer, BaseCollection, CollectionBuilder
from binx.exceptions import InternalNotDefinedError, CollectionLoadError

from marshmallow import fields
from marshmallow.exceptions import ValidationError

from pprint import pprint


class TestCollectionBuilder(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def make_dynamic_class(self):

        class A(object):
            pass

        ASubClass = CollectionBuilder._make_dynamic_class('ASubClass', ('arg1','arg2',), base_class=A)
        self.assertEqual(str(ASubClass.__bases__[0]),"<class 'tests.test_builder.TestCollectionBuilder.test_make_internal_obj_.<locals>.A'>")

        a = ASubClass(arg1='a', arg2='b')
        self.assertEqual(a.__dict__, {'arg2': 'b', 'arg1': 'a'})

        with self.assertRaises(TypeError):
            b = ASubClass(arg3='a')
