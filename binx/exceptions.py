""" Custom exceptions for binx
"""

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
