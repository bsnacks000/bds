from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import unittest
import os

from binx.registry import register_internal, get_class_from_internal_registry, get_class_from_collection_registry
from binx.collection import InternalObject
from binx.exceptions import InternalRegistryError

from pprint import pprint

class TestInternal(InternalObject):

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c


class TestRegistry(unittest.TestCase):


    def setUp(self):
        self.internal = TestInternal(1,2,3)  # should register the internal


    def test_internal_object_is_registered_via_metaclass(self):

        module = self.internal.__module__ # use the path name of the internal object on setUp
        clsname = TestInternal.__name__
        obj = get_class_from_internal_registry('.'.join([module, clsname]))

        self.assertIsInstance(obj(4,5,6), TestInternal)


    def test_internal_registry_raises_InternalRegistryError_if_not_in_registry(self):

        with self.assertRaises(InternalRegistryError):
            obj = get_class_from_internal_registry('SomeClass')


    def test_registry_raises_if_two_classes_have_same_name(self):

        with self.assertRaises(InternalRegistryError):

            # NOTE user  cannot declare two classes in the same module
            class TestA(InternalObject):
                pass

            class TestA(InternalObject):
                pass
