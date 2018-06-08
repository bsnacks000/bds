
from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import unittest
import os

from binx.collection import InternalObject, BaseSerializer, BaseCollection, CollectionBuilder
from binx.exceptions import InternalNotDefinedError, CollectionLoadError

from marshmallow import fields

from pprint import pprint



class TestSerializer(BaseSerializer):

    x = fields.Integer()
    y = fields.Integer()
    z = fields.Str()



class TestInternal(InternalObject):

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class TestCollectionBuilder(unittest.TestCase):

    def setUp(self):
        self.coll_builder = CollectionBuilder('Test')

    def tearDown(self):
        self.coll_builder.name = 'Test'

    def test_make_dynamic_class(self):

        class A(object):
            pass

        ASubClass = self.coll_builder._make_dynamic_class('ASubClass', ('arg1','arg2',), base_class=A)
        self.assertEqual(str(ASubClass.__bases__[0]),"<class 'tests.test_builder.TestCollectionBuilder.test_make_dynamic_class.<locals>.A'>")

        a = ASubClass(arg1='a', arg2='b')
        self.assertEqual(a.__dict__, {'arg2': 'b', 'arg1': 'a'})

        with self.assertRaises(TypeError):
            b = ASubClass(arg3='a')


    def test_make_collection_class(self):

        TestCollection = self.coll_builder._make_collection_class('Test', TestSerializer, TestInternal)

        t = TestCollection()
        self.assertIsInstance(t, BaseCollection)
        self.assertIn('internal_class',TestCollection.__dict__)
        self.assertIn('serializer_class', TestCollection.__dict__)
        self.assertIsInstance(t.serializer, TestSerializer)
        self.assertIsInstance(t.internal_class(1,2,3), TestInternal)

    def test_get_declared_fields(self):

        declared = self.coll_builder._get_declared_fields(TestSerializer)
        self.assertEqual(set(['x', 'y', 'z']), set(declared))


    def test_parse_names(self):
        coll_name, internal_name = self.coll_builder._parse_names('Thing')

        self.assertEqual(coll_name, 'ThingCollection')
        self.assertEqual(internal_name, 'ThingInternal')

    def test_build(self):

        class TestAgainSerializer(BaseSerializer):

            x = fields.Integer()
            y = fields.Integer()
            z = fields.Str()

        self.coll_builder.name = 'TestAgain'
        TestCollection = self.coll_builder.build(TestAgainSerializer)

        self.assertIsInstance(TestCollection(), BaseCollection)

    def test_build_internal_only_builds_and_registers_internal(self):

        class TestAgainAgainSerializer(BaseSerializer):

            x = fields.Integer()
            y = fields.Integer()
            z = fields.Str()

        self.coll_builder.name = 'TestAgainAgain'
        InternalOutput = self.coll_builder.build(TestAgainAgainSerializer, internal_only=True)

        self.assertIsInstance(InternalOutput(), InternalObject)
