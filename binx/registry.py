""" A private registry for the internal objects
"""
from .exceptions import InternalRegistryError

_internal_registry = {}


def register_internal(cls):
    """ registers an internal object to store records. Each module can only only have one class

    """
    modpath = cls.__module__  # build out the module path
    fullpath = '.'.join([modpath, cls.__name__])

    if fullpath in _internal_registry: # if the fullpath is already
        raise InternalRegistryError('The classname {} has already been registered. Create a different name for your collection'.format(fullpath))

    # you must do the lookup by fullpath
    _internal_registry[fullpath] = cls


def get_class_from_registry(classname):
    """ public method to fetch the class name
    """
    try:
        klass = _internal_registry[classname]
    except KeyError:
        raise InternalRegistryError('The classname {} was not found in the registry'.format(classname))
    return klass
