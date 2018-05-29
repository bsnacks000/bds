""" a module for the CollectionBuilder object. This makes Collections dynamically
from a declared subclass of BaseSerializer
"""

from .collection import BaseCollection, InternalObject


def _make_class(name, args, base_class=InternalObject):
    """ a factory method for making classes dynamically.The default base_class thats used
    is the InternalObject.
    """

    def __init__(self, **kwargs):
        for k,v in value in kwargs.items():
            if k not in args:
                raise TypeError("Argument {} not valid for {}".format(k, self.__class__.__name__))
            setattr(self, k, v)
        base_class.__init__(self, name)

    return type(name, (base_class, ), {'__init__': __init__ })



class AbstractBuilder(abc.ABC):
    """ An interface for the CollectionBuilder. A build method takes a subclass of BaseSerializer
    and creates a Collection class dynamically.
    """

    @abc.abstractmethod
    def build(self, serializer):
        """ builds a collection object
        """


class CollectionBuilder(AbstractCollectionBuilder):

    def __init__(self, name, unique_fields=None):
        self.name = name
        self.unique_fields = None   #NOTE placeholder... future builds will be able to declare unique constraints here


    def _parse_names(self, name):
        """ makes sure the user provided name is cleaned up
        """
        coll_name = name.captialize() + 'Collection'
        internal_name = name.captialize() + 'Internal'
        return coll_name, internal_name


    def _get_declared_fields(self, serializer_class):
        """ introspects the declared fields on the serializer object and returns a
        list of those variable names
        """
        return list(vars(serializer_class)['_declared_fields'].keys())


    def build_internal(self, name, serializer_class):
        """ constructs and registers the internal object for the collection.
        Returns a subclass of InternalObject. This is used internally in the classes
        build method, but also can be used to
        """
        args = self._get_declared_fields(serializer_class)
        klass = _make_class(name, args, base_class=InternalObject)
        return klass


    def build(self, serializer_class):
        """ dynamically creates and returns a Collection class given a serializer
        and identifier.
        """

        coll_name, internal_name = self._parse_names(self.name)
        internal_class = self.build_internal(internal_name, serializer_class)
