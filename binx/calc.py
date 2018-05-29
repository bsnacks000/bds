""" Defines an abstract base class for all calc objects
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *

import abc

class AbstractCalc(abc.ABC):
    """An abstract calc is a callable that returns a result object specific to the
    subclass. Each data structure in a result is unique, but must be serializable into
    a flat or nested dictionary.
    """

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """ Run all internal methods and generate a result object, passing in
        any neccessary parameters that have not yet been initialized on the class
        """


class AbstractCalcResult(abc.ABC):
    """ A containor object for Calc Results. A method that serializes the calc data must
    be implemented.
    """

    @abc.abstractmethod
    def serialize(self):
        """ serializes the results into a json-serializable dictionary or list of dictionaries
        """
