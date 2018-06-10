""" A private registry for the collection objects. It is mainly used to register
adaption classes on each collection object for data cleaning/processing. The classes
are created by the user and registered at runtime.
"""

from .exceptions import RegistryError


_collection_registry = {}


def register_collection(cls):
    """ registers a new collection class.
    """

    modpath = cls.__module__  # build out the module path
    fullpath = '.'.join([modpath, cls.__name__])

    if fullpath in _collection_registry: # if the fullpath is already
        raise RegistryError('The classname {} has already been registered. Create a different name for your collection'.format(fullpath))

    # you must do the lookup by fullpath
    _collection_registry[fullpath] = (cls, {
        'serializer_class': cls.serializer_class,
        'internal_class': cls.internal_class,
        'registered_adapters': [],  #NOTE these are the classes registered adapters
        'adaptable_from': []   #NOTE these are other collection objects a coll can be adapted from
    })


def get_class_from_collection_registry(classname):
    """ returns the full tuple given the fully qualified classname
    """
    try:
        klass_tuple = _collection_registry[classname]
    except KeyError:
        raise RegistryError('The classname {} was not found in the registry'.format(classname))
    return klass_tuple


def register_adapter_to_collection(classname, adapter):
    """ appends an adapter to the klass object
    """
    _collection_registry[classname][1]['registered_adapters'].append(adapter)


def register_adaptable_collection(classname, coll):
    """ appends an adaptable collection to a classes list of adaptable collections
    """
    _collection_registry[classname][1]['adaptable_from'].append(coll)
