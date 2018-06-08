""" Abstract base classes for the system. The AHUOb
"""
from __future__ import unicode_literals, absolute_import, division, print_function
from builtins import *

import abc
import pandas as pd
from marshmallow import Schema, post_load
from marshmallow.exceptions import ValidationError

from .exceptions import InternalNotDefinedError, CollectionLoadError

from .registry import register_internal

from .utils import DataFrameDtypeConversion

import logging
l = logging.getLogger(__name__)

# a place for the registry of internals after they are constructed


class InternalMeta(type):
    """ a metaclass that adds the internal object to a registry
    """

    def __new__(cls, klassname, bases, attrs):
        klass = super().__new__(cls, klassname, bases, attrs)
        register_internal(klass)  # here is your register function
        return klass


class InternalObject(metaclass=InternalMeta):
    """ a namespace/base class for instance checking for an internally used model object
    It is otherwise a normal python object. _Internals are used as medium for
    serialization and deserialization and their declarations bound with Collections and enforced by Serializers
    """

    def __init__(self, **kwargs):
        # NOTE that this method will get overridden in the make_class factory method below
        self.__dict__.update(**kwargs)

    def __repr__(self):
        """ default is to print all available attrs in vars
        """
        name = "<{} ".format(self.__class__.__name__)
        for k, attr in vars(self).items():
            name += "{}: {}, ".format(k, attr)
        name += ">"
        return name



class BaseSerializer(Schema):

    def __init__(self, *args, **kwargs):
        """ overrides Schema to include a internal object. These are instantiated with the serializer
        and used for loading and validating data
        """
        if 'internal' in kwargs:
            self._InternalClass = kwargs.pop('internal')
        else:
            raise InternalNotDefinedError('An InternalObject class must be instantiated with this Collection')

        super(Schema, self).__init__(*args, **kwargs)


    @post_load
    def load_object(self, data):
        """ loads and validates an internal class object """
        return self._InternalClass(**data)


class AbstractCollection(abc.ABC):
    """Defines an interface for Collection objects. This includes a valid marshmallow
    serializer class, a data list object iterablem, load_data method with validation
    """


    @property
    @abc.abstractmethod
    def serializer_class(self):
        """ returns an ma serializer. Used for validation and instantiation """



    @property
    @abc.abstractmethod
    def internal_class(self):
        """ returns an ma serializer. Used for validation and instantiation
        NOTE possibly change to class method
        """


    @property
    @abc.abstractmethod
    def data(self):
        """ returns an object-representation of the metadata using the serializer
        """


    @abc.abstractmethod
    def load_data(self, object):
        """ uses a marshmallow serializer to validate and load the data into an object-record
        representation
        """

    @abc.abstractmethod
    def to_dataframe(self):
        """ returns a dataframe representation of the object. This wraps the data property in a pd.DataFrame
        """

    @abc.abstractmethod
    def to_json(self):
        """ returns a json string representation of the data using the serializer
        """


class BaseCollection(AbstractCollection):
    """ Used to implement many of the default AbstractCollection methods
    Subclasses will mostly just need to define a custom Serializer and InternalObject pair
    """
    serializer_class = BaseSerializer   # must be overridden with a valid marshmallow schema and _Internal
    internal_class = InternalObject

    def __init__(self):
        self._data = []
        self._serializer = self.serializer_class(internal=self.__class__.internal_class, strict=True)


    @property
    def serializer(self):
        """ returns an ma serializer. Used for validation and instantiation """
        return self._serializer


    @property
    def data(self):
        """ returns an object-representation of the metadata using the serializer
        """
        if len(self._data) == 0:
            return self._data
        marshal_result = self.serializer.dump(self._data, many=True) # NOTE returns MarshalResult object
        return marshal_result.data  # NOTE differs from 3.0.0 -- only returns records here

    @property
    def internal_class(self):
        """ returns a class of the internal object
        """
        return self.__class__.internal_class


    def __iter__(self):
        self._idx = 0
        return self


    def __next__(self):
        self._idx += 1
        if self._idx > len(self._data):
            raise StopIteration
        return self._data[self._idx-1]


    def __len__(self):
        return len(self._data)


    def __getitem__(self, i):
        return self._data[i]


    def __add__(self, other):
        if isinstance(other, self.__class__):
            combined = self.data + other.data
            new_inst = self.__class__()
            new_inst._data = combined
            return new_inst
        else:
            raise TypeError('Only Collections of the same class can be concatenated')


    def load_data(self, records, from_df=False):
        """default implementation. Defaults to handling lists of python-dicts (records). from_df=True will allow
        direct from dataframe serialization as a convenience
        #TODO -- create a drop_duplicates option and use pandas to drop the dupes
        """
        try:
            if from_df:
                util = DataFrameDtypeConversion()
                records = util.df_nan_to_none(records)
                records = records.to_dict('records')

            # append to the data dictionary
            # NOTE changing this to handle tuples in marsh 2.x
            valid, _ = self.serializer.load(records, many=True)
            self._data += valid

        except TypeError as err:
            l.error(err)
            raise CollectionLoadError('A Serializer must be instantiated with valid fields') from err

        except ValidationError as err:
            errors = err.messages
            l.error(errors)
            raise

        except Exception as err:
            l.error(err)
            raise CollectionLoadError('An error occurred while loading and validating records') from err


    def to_dataframe(self):
        """ returns a dataframe representation of the object. This wraps the data property in a
        pd.DataFrame
        converts any columns that can be converted to datetime
        """
        df = pd.DataFrame(self.data)
        df = df.apply(lambda col: pd.to_datetime(col, errors='ignore') if col.dtypes == object else col, axis=0)
        return df


    def to_json(self):
        """ returns a json string representation of the data using the serializer
        """
        return self.serializer.dumps(self._data, many=True)







class AbstractCollectionBuilder(abc.ABC):
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


    def _make_dynamic_class(self, name, args, base_class=InternalObject):
        """ a factory method for making classes dynamically.The default base_class thats used
        is the InternalObject. NOTE args is an iterable
        """

        def __init__(self, **kwargs):
            base_class.__init__(self)
            for k,v in kwargs.items():
                if k not in args:
                    raise TypeError("Argument {} not valid for {}".format(k, self.__class__.__name__))
                setattr(self, k, v)
        return type(name, (base_class, ), {'__init__': __init__ })


    def _make_collection_class(self, name, serializer_class, internal_class, base_class=BaseCollection):
        """ specifically makes collection classes by assigning the two necessary class attributes
        """
        class_attrs = {'serializer_class': serializer_class, 'internal_class': internal_class}
        return type(name, (base_class, ), class_attrs)


    def _parse_names(self, name):
        """ makes sure the user provided name is cleaned up
        """
        coll_name = name.capitalize() + 'Collection'
        internal_name = name.capitalize() + 'Internal'
        return coll_name, internal_name


    def _get_declared_fields(self, serializer_class):
        """ introspects the declared fields on the serializer object and returns a
        list of those variable names
        """
        return list(vars(serializer_class)['_declared_fields'].keys())


    def _build_internal(self, name, serializer_class):
        """ constructs and registers the internal object for the collection.
        Returns a subclass of InternalObject. This is used internally in the classes
        build method, but also can be used to
        """
        args = self._get_declared_fields(serializer_class)
        klass = self._make_dynamic_class(name, args, base_class=InternalObject)
        return klass


    def build(self, serializer_class, internal_only=False):
        """ dynamically creates and returns a Collection class given a serializer
        and identifier.
        """

        coll_name, internal_name = self._parse_names(self.name) # create the col name
        internal_class = self._build_internal(internal_name, serializer_class) # create the internal class

        if internal_only:
            return internal_class

        return self._make_collection_class(coll_name, serializer_class, internal_class, base_class=BaseCollection) # pass in the serializer
