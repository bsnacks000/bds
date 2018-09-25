""" Abstract base classes for the system. The AHUOb
"""

import abc
import pandas as pd
import numpy as np
from marshmallow import Schema, post_load, fields
from marshmallow.exceptions import ValidationError

from .exceptions import InternalNotDefinedError, CollectionLoadError, CollectionValidationError, AdapterChainError
from .registry import register_collection, get_class_from_collection_registry, adapter_path
from .utils import DataFrameDtypeConversion, RecordUtils

import logging
l = logging.getLogger(__name__)



# a place for the registry of internals after they are constructed


class InternalObject(object):
    """ a namespace class for instance checking for an internally used model object
    It is otherwise a normal python object. _Internals are used as medium for
    serialization and deserialization and their declarations bound with Collections and enforced by Serializers.
    It can be inherited from or used as a Mixin.
    """
    is_binx_internal = True
    registered_colls = set()   #NOTE these are collections. A coll's metaclass hook appends any collection objects here

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

class BaseSerializer(Schema):
    """The BaseSerializer overrides Schema to include a internal to dump associated InternalObjects.
    These are instantiated with the serializer and used for loading and validating data.
    It also provides a mapping of numpy dtypes to a select amount of marshmallow field name which helps optimize
    memory in the to_dataframe object
    """

    registered_colls = set()

    numpy_map = {

        fields.Integer: np.dtype('int'),
        fields.Float: np.dtype('float'),
        fields.Str: np.dtype('str'),
        fields.Date: np.dtype('datetime64[ns]'),
        fields.DateTime: np.dtype('datetime64[ns]'),
        fields.List: np.dtype('O'),
        fields.Bool: np.dtype('bool'),
        fields.Dict: np.dtype('O'),
        fields.Nested: np.dtype('O')

    }


    def __init__(self, *args, **kwargs):

        if 'internal' in kwargs:
            self._InternalClass = kwargs.pop('internal')
        else:
            raise InternalNotDefinedError('An InternalObject class must be instantiated with this Collection')

        super(Schema, self).__init__(*args, **kwargs)

        self.dateformat_fields = self._set_dateformat_fields()


    def _set_dateformat_fields(self):
        """ builds a mapping of date formatted column names to string formats for Collection.load_data
        """
        dateformat_fields = {}
        for col,field in self.fields.items():
            if isinstance(field, fields.DateTime):
                if field.dateformat is not None:
                    dateformat_fields[col] = field.dateformat
            elif isinstance(field, fields.Date):
                if hasattr(field, 'dateformat'):
                    dateformat_fields[col] = field.dateformat
                else:
                    dateformat_fields[col] = '%Y-%m-%d' # we set this as a default for datetime.date based objects
        return dateformat_fields


    @post_load
    def load_object(self, data):
        """ loads and validates an internal class object """
        return self._InternalClass(**data)


    def get_numpy_fields(self):
        """ returns a dictionary of column names and numpy dtypes based on the ma_np_map dictionary.
        Collections will use this to create more mem-optimized dataframes
        """
        out = {}
        for field_name in self._declared_fields.keys():
            ma_klass = self.__class__._declared_fields[field_name]
            out[field_name] = self.numpy_map.get(type(ma_klass)) or np.dtype('O')
        return out


class CollectionMeta(type):

    def __new__(cls, classname, bases, attrs):
        klass = super().__new__(cls, classname, bases, attrs)
        register_collection(klass)
        return klass

# compose a mixed Metaclass that registers and provides an abstract interface
AbstractCollectionMeta = type('AbstractCollectionMeta', (abc.ABC, CollectionMeta), {})

class AbstractCollection(object, metaclass=AbstractCollectionMeta):
    """Defines an interface for Collection objects. This includes a valid marshmallow
    serializer class, a data list object iterablem, load_data method with validation.
    Collections are also registered so this AbstractCollection uses AbstractCollectionMeta as
    a metaclass
    """

    @abc.abstractmethod
    def get_fully_qualified_class_path(self):
        """ reaches into the registry and gets the fully qualified class path"""


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

    def __new__(cls, *args, **kwargs):
        cls.serializer_class.registered_colls.add(cls)  #NOTE add a new subclass collection to the internal and internal class
        cls.internal_class.registered_colls.add(cls)
        inst = super(BaseCollection, cls).__new__(cls, *args, **kwargs)
        return inst


    def __init__(self):
        self._data = []
        self._serializer = self.serializer_class(internal=self.__class__.internal_class, strict=True)


    @classmethod
    def get_fully_qualified_class_path(cls):
        """ This returns the fully qualified class name for this class. This can be used for collection_registry lookup
        """
        return cls.__module__ + '.' + cls.__name__

    @classmethod
    def get_registry_entry(cls):
        """ This returns the complete registry entry for this class
        """
        return get_class_from_collection_registry(cls.get_fully_qualified_class_path())


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
    def internal(self):
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
            new_inst.load_data(combined)
            return new_inst
        else:
            raise TypeError('Only Collections of the same class can be concatenated')

    @classmethod
    def _resolve_adapter_chain(cls, input_collection, **adapter_context):
        """ attempts to resolve the adapter chain using the current class as the target and
        input as the starting class. The adapter context accumulates over each call and ensures that
        kwargs needed for certain adapter calls are guaranteed to make it to the correct adapter.

        returns the final AdapterOutputContainer with accumulated context or None if there are no adapters in the adapter chain
        This raises an AdapterChainError in adapt
        """
        adapters = adapter_path(input_collection.__class__, cls)
        if len(adapters) == 0:  # return an empty list if no adapters can be found
            return

        current_context = adapter_context  # set starting point... these are instances and will be modified below
        current_input = input_collection  # NOTE this is an instance with data to be transformed.. not a class
        adapter_output = None

        for adapter_class in adapters:
            #NOTE custom error handling must be added here
            current_adapter = adapter_class() # for each adapter class we push the input_collection and a context
            adapter_output = current_adapter(current_input, **current_context) # adapt data to the next type of collection
            current_context = {**current_context, **adapter_output.context} # NOTE this is will fail on py3.4
            current_input = adapter_output.collection

        adapter_output._context = current_context
        return adapter_output

    def _dataframe_with_dtypes(self, data):
        """ converts records to column format
        """
        rutil = RecordUtils()
        dfutil = DataFrameDtypeConversion()
        col_data = rutil.records_to_columns(data)
        dtype_map = self.serializer.get_numpy_fields()

        # iterate columns and construct a dictionary of pd.Series with correct-dtype
        df_data = {} # a dictionary of pd.Series with dtypes keyed by col names
        for col, dtype in dtype_map.items():
            try:
                df_data[col] = pd.Series(col_data[col], dtype=dtype)
            except KeyError as err:
                l.warning('Creating df without non-required field {}'.format(col))
                pass 

        df = pd.DataFrame(df_data)
        df = dfutil.df_none_to_nan(df)
        return df


    def _clean_dataframe(self, df):
        """ cleans and converts formats on a dataframe
        """
        formatfields = self.serializer.dateformat_fields

        util = DataFrameDtypeConversion()
        df = util.df_nan_to_none(df)
        if len(formatfields) > 0:
            date_col_mapping = self.serializer.dateformat_fields
            df = util.date_to_string(formatfields, df)

        records = df.to_dict('records')
        return records

    def _clean_records(self, records):
        formatfields = self.serializer.dateformat_fields

        util = RecordUtils()
        #TODO should check nans here but need a faster algo

        if len(formatfields) > 0:
            records = util.date_to_string(formatfields, records)

        return records


    def load_data(self, records):
        """default implementation. Defaults to handling lists of python-dicts (records).
        #TODO -- create a drop_duplicates option and use pandas to drop the dupes
        """
        try:
            if isinstance(records, pd.DataFrame):
                records = self._clean_dataframe(records)
            else:
                records = self._clean_records(records)

            # append to the data dictionary
            # NOTE changing this to handle tuples in marsh 2.x
            valid, _ = self.serializer.load(records, many=True)
            self._data += valid

        except TypeError as err:
            raise CollectionLoadError('A Serializer must be instantiated with valid fields') from err

        except ValidationError as err:
            errors = err.messages
            l.error(errors)
            raise CollectionValidationError('A ValidationError occurred while trying to load {}'.format(self.__class__.__name__)) from err

        except Exception as err:
            raise CollectionLoadError('An error occurred while loading and validating records') from err


    @classmethod
    def adapt(cls, input_collection, **adapter_context):
        """ Attempts to adapt the input collection instance into a collection of this type by
        resolving the adapter chain for the input collection. Any kwargs passed in are handed over to the resolver.
        colla = CollectionA()
        colla.load_data(some_data)
        collb, context = CollectionB.adapt(colla, some_var=42, some_other_var=66)


        This method returns a new instance of the adapted class (the caller)
        """
        if not issubclass(input_collection.__class__, BaseCollection): #check if its a Collection or raise TypeError
            raise TypeError('The input to adapt must be a Collection')
        try:
            adapted = cls._resolve_adapter_chain(input_collection, **adapter_context) # attempt to resolve the adapter chain
        except Exception as err:
            raise AdapterChainError('An error occured within the adapter chain') from err

        if adapted is not None:
            return adapted.collection, adapted.context # on success we return the new collection and the accumulated context for reference
        else:
            raise AdapterChainError('The input_collection {} could not be found on the adapter chain for {}'.format(
                input_collection.__class__.__name__, cls.__name__))


    def to_dataframe(self):
        """ returns a dataframe representation of the object. This wraps the data property in a
        pd.DataFrame
        converts any columns that can be converted to datetime
        """
        return self._dataframe_with_dtypes(self.data)


    def to_json(self):
        """ returns a json string representation of the data using the serializer
        """
        return self.serializer.dumps(self._data, many=True)




class AbstractCollectionBuilder(abc.ABC):
    """ An interface for the CollectionBuilder. A build method takes a subclass of BaseSerializer
    and creates a Collection class dynamically. Its use is optional but is designed to cut down on
    class declarations if the user is making many generic Collection implementations.
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
        x =  type(name, (base_class, ), class_attrs)
        return x

    def _parse_names(self, name):
        """ makes sure the user provided name is cleaned up
        """
        coll_name = name + 'Collection'
        internal_name = name+ 'Internal'
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
        and identifier. If internal_only is set to True then this will only return the internal.
        This is useful if you are using a declarative approach to defining the collections and want to
        add or override some of the base behavior

        """

        coll_name, internal_name = self._parse_names(self.name) # create the col name
        internal_class = self._build_internal(internal_name, serializer_class) # create the internal class

        if internal_only:
            return internal_class

        return self._make_collection_class(coll_name, serializer_class, internal_class, base_class=BaseCollection) # pass in the serializer
