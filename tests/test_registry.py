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


    def test_registry_raises_if_two_classes_have_same_name(self):

        with self.assertRaises(RegistryError):

            # NOTE user  cannot declare two classes in the same module
            class TestBaseA(BaseCollection):
                pass

            class TestBaseA(BaseCollection):
                pass

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
