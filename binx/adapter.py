""" The adapter module helps the user mutate one collection into another. This works similar to
a calc class in calc_factory.
BaseAdapter's call takes a collection's data attribute as the first argument. An adapt() method is overridden
by the user which must return a serializable object.

Once the class is declared the user register's the adapter using the register static method.
"""
import abc
import json

from .registry import get_class_from_collection_registry, register_adapter_to_collection, \
    register_adaptable_collection


def check_serializable(method):
    """ this checks on the call method to make sure the result can be serialized
    as a list of dicts
    """
    def inner(*args, **kwargs):
        result = method(*args, **kwargs)

        try:
            assert type(result) == list
            json.dumps(result)
            return result

        except (AssertionError, TypeError) as err:
            raise err('adapt must return a JSON serializable object in record format (list of dicts)')



class AbstractAdapter(abc.ABC):

    @abc.abstractmethod
    def adapt(self, data, *args, **kwargs):
        """ The user must overrides this method to do the data cleaning. Any additional methods
        needed for cleaning should be considered private to the Adapter subclass
        """

    @check_serializable
    def __call__(self, data, *args, **kwargs):
        result = self.adapt(data, *args, **kwargs)
        return result



def register_adapter(adapter_class, from_class, target_class):
    """ Assigns the adapter class a target and from class. And registers the link in the
    collection class registry.
    """
    adapter_class.target_class = target_class  # assign the class a from and target
    adapter_class.from_class = from_class

    target_lookup_path = target_class.get_fully_qualified_class_path()  # get some path names
    from_lookup_path = from_class.get_fully_qualified_class_path()

    # register adapter to the 'from' classes 'adapters' list and link the two classes on the 'target'
    # in its 'adaptable_from' list
    register_adapter_to_collection(from_class, adapter)
    register_adaptable_collection(target_class, from_class)
