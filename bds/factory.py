""" Base classes that interact with calc objects and collections and form the user/client-level API

"""
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *

import abc
from .exceptions import FactoryCreateValidationError
from marshmallow.exceptions import ValidationError

import logging
l = logging.getLogger(__name__)



class AbstractBaseFactory(abc.ABC):
    """ AbstractBase class for Factory classes. Enforces implementation of the load _processor and create methods
    A Factory class is responsible for using an input Collection object
    to create a new output collection object. Its repsonsible for changing the
    state of the system. Each CalcObject will have a corresponding Factory
    class whose attributes are unique to that state.
    """

    @property
    @abc.abstractmethod
    def calc(self):
        """ an instance of a calc object. Used by process to return a CalcResult object. This
        class is defined on the Factory class and instantiated privately in the
        factory's __init__ method with any neccessary settings.
        """

    @property
    @abc.abstractmethod
    def output_collection(self):
        """an instance collection class that is generated by the factory's create method.
        """

    @abc.abstractmethod
    def load(self, *args):
        """ The load method should take an iterable of Collection instances.
        After passing a type check these collections should stored on the instance. Each
        factory subclass will have different requirements and therefore different collection attributes
        """


    @abc.abstractmethod
    def _processor(self, **kwargs):
        """ the main processing logic in the factory. Responsible for loading and running
        the factory's calc object with the given settings and data. This implementation can
        vary depending on the calc being performed but should return a list of CalcResult objects.
        Any exceptions on the calc class are caught, wrapped and handled in create.
        """


    @abc.abstractmethod
    def create(self, **kwargs):
        """ Calls _processor, parses results and creates a new Collection using the
        the Collection set on the class. Responsible for loading data. Will return a new collection
        or raise either a CalcError or ValidationError
        """




class BaseFactory(AbstractBaseFactory):
    """
    Implements most of the methods above. Subclasses just need to inherit from this
    class and override load and process with unique implementations.
    A calc class, input_collection_class and output_collection_class must be set
    on subclasses. CalcClass, OutputCollectionClass and InputCollectionClasses must be
    set on the subclass.
    """
    CalcClass = None # the calc object associated with
    OutputCollectionClass = None  # the output collection class type. Instantiated and appended to on __init__


    def __init__(self, **kwargs):
        self._calc = self.CalcClass(**kwargs)
        self._output_collection = self.OutputCollectionClass()

    @property
    def calc(self):
        """an instance of a calc object. Used by process to return a CalcResult object. This
        class is defined on the Factory class and instantiated privately in the
        factory's __init__ method with any neccessary settings.
        """
        return self._calc


    @property
    def output_collection(self):
        """an instance collection class that is generated by the factory's create method.
        """
        return self._output_collection


    def load(self, collection):
        """load method must be overridden in subclasses.
        NOTE this is a no-op in the base class
        """
        raise NotImplementedError('Subclasses must implement load')


    def _processor(self, **kwargs):
        """ _processor method must be overridden in subclasses
        """
        raise NotImplementedError('Subclasses must implement _processor')


    def create(self, reset=True, **settings):
        """ create a new collection using the _processor method. kwargs are any settings or additional data
        that the factory processor needs
        If the reset flag is set to False, then further calls to create will accumulate results on the same
        collection. The default behavior is to create a new OutputCollection Instance
        """
        try:
            if reset:
                self._output_collection = self.OutputCollectionClass() # reset the output collection if desired

            output = self._processor(**settings)  #NOTE returns serialized record list for the collection here
            self.output_collection.load_data(output) #NOTE load serialized record list

            return self.output_collection

        except ValidationError as err:
            raise FactoryCreateValidationError('A validation occured while creating the  collection') from err # wrap a marshmallow ValidationError
