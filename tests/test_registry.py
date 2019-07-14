from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import unittest
import os

from binx.registry import get_class_from_collection_registry, register_adapter_to_collection, register_adaptable_collection
from binx.collection import InternalObject, BaseSerializer, BaseCollection
from binx.exceptions import RegistryError

from pprint import pprint

from marshmallow import fields


# some mocks here...
class TestCollRegistrySerializer(BaseSerializer):
    a = fields.Integer()

class TestCollRegistryInternal(InternalObject):
    def __init__(self, a):
        self.a = a

class TestRegistryCollection(BaseCollection):
    serializer_class = TestCollRegistrySerializer
    internal_class = TestCollRegistryInternal


class TestRegistry(unittest.TestCase):

    def test_internal_registry_raises_InternalRegistryError_if_not_in_registry(self):

        with self.assertRaises(RegistryError):
            obj = get_class_from_collection_registry('SomeClass')


    def test_registry_override_raises_registry_error_if_has_adaptable_collections(self):

        class TestBaseA(BaseCollection):
            pass

        register_adaptable_collection(TestBaseA.get_fully_qualified_class_path(), 'something')
        with self.assertRaises(RegistryError):
            class TestBaseA(BaseCollection):
                pass


    def test_registry_override_raises_registry_error_if_has_registered_adapters(self):

        class TestBaseAA(BaseCollection):
            pass

        register_adapter_to_collection(TestBaseAA.get_fully_qualified_class_path(), 'something')
        with self.assertRaises(RegistryError):
            class TestBaseAA(BaseCollection):
                pass


    def test_registry_warns_and_replaces_ref_if_given_same_path(self):

        with self.assertWarns(UserWarning):
            class TestBaseReplaceMe(BaseCollection):
                a = 1

            class TestBaseReplaceMe(BaseCollection):
                a = 42

            module = TestBaseReplaceMe.__module__
            clsname = TestBaseReplaceMe.__name__

            TestClass = get_class_from_collection_registry('.'.join([module, clsname]))

            self.assertEqual(42, TestClass[0].a)


    def test_collection_registry(self):

        module = TestRegistryCollection.__module__ # use the path name of the internal object on setUp
        clsname = TestRegistryCollection.__name__

        obj = get_class_from_collection_registry('.'.join([module, clsname]))
        self.assertIsInstance(obj[0](), TestRegistryCollection)  # the class itself
        self.assertEqual(obj[1]['serializer_class'].__bases__[0], BaseSerializer)
        self.assertEqual(obj[1]['internal_class'].__bases__[0], InternalObject)

    def test_register_adaptor_to_collection(self):

        class DummyAdaptor(object):
            pass

        module = TestRegistryCollection.__module__ # use the path name of the internal object on setUp
        clsname = TestRegistryCollection.__name__
        full = '.'.join([module,clsname])

        register_adapter_to_collection(full, DummyAdaptor)
        obj = get_class_from_collection_registry(full)
        test = DummyAdaptor in obj[1]['registered_adapters']
        self.assertTrue(test)


    def test_register_adaptable_collection(self):

        class TestAnotherCollRegistrySerializer(BaseSerializer):
            a = fields.Integer()

        class TestAnotherCollRegistryInternal(InternalObject):
            def __init__(self, a):
                self.a = a

        class TestAnotherRegistryCollection(BaseCollection):
            serializer_class = TestAnotherCollRegistrySerializer
            internal_class = TestAnotherCollRegistryInternal

        module = TestRegistryCollection.__module__ # use the path name of the internal object on setUp
        clsname = TestRegistryCollection.__name__
        full = '.'.join([module,clsname])

        register_adaptable_collection(full, TestAnotherRegistryCollection)
        obj = get_class_from_collection_registry(full)
        test = TestAnotherRegistryCollection in obj[1]['adaptable_from']
        self.assertTrue(test)
