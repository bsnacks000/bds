""" Custom exceptions for binx
"""
from marshmallow.exceptions import ValidationError

class BinxError(Exception):
    """ A base exception for the library
    """

class InternalNotDefinedError(BinxError):
    """ used for development - thrown if an Internal class is improperly declared on a Collection"""


class CollectionLoadError(BinxError):
    """ thrown if a Collection fails to load its Internal Object Collection this could be due to a validation error or some other issue """


class FactoryProcessorFailureError(BinxError):
    """ raised if the _process method of a Factory fails to produce any results
    """

class FactoryCreateValidationError(BinxError):
    """ wraps a marshmallow validation error in the create method of the factory
    """



class RegistryError(BinxError, KeyError):
    """ raised if a classname already exists in the collection registry
    """


class CollectionValidationError(ValidationError, BinxError):
    """ subclass of a marshmallow validation error
    """

class AdapterCollectionResultError(BinxError):
    """ thrown if a collection load fails while attempting to adapt
    """

class AdapterChainError(BinxError):
    """ thrown if a input collection cannot be found on the adapter chain for a Collection
    """
