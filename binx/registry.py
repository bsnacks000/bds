""" A private registry for the internal objects
"""
from .exceptions import InternalRegistryError, CollectionRegistryError

_internal_registry = {}
_collection_registry = {}


def register_internal(cls):
    """ registers an internal object to store records. Each module can only only have one class
    """
    modpath = cls.__module__  # build out the module path
    fullpath = '.'.join([modpath, cls.__name__])

    if fullpath in _internal_registry: # if the fullpath is already
        raise InternalRegistryError('The classname {} has already been registered. Create a different name for your collection'.format(fullpath))

    # you must do the lookup by fullpath
    _internal_registry[fullpath] = cls


def register_collection(cls):
    """ registers a new collection class
    """

    modpath = cls.__module__  # build out the module path
    fullpath = '.'.join([modpath, cls.__name__])

    if fullpath in _internal_registry: # if the fullpath is already
        raise CollectionRegistryError('The classname {} has already been registered. Create a different name for your collection'.format(fullpath))

    # you must do the lookup by fullpath
    _collection_registry[fullpath] = (cls, {
        'serializer_class': cls.serializer_class,
        'internal_class': cls.internal_class,
        'registered_adaptors': [],
        'registered_adaptable_collections': []
    })



def get_class_from_internal_registry(classname):
    """ public method to fetch the class name
    """
    try:
        klass = _internal_registry[classname]
    except KeyError:
        raise InternalRegistryError('The classname {} was not found in the registry'.format(classname))
    return klass


def get_class_from_collection_registry(classname):

    try:
        klass = _collection_registry[classname]
    except KeyError:
        raise CollectionRegistryError('The classname {} was not found in the registry'.format(classname))
    return klass
