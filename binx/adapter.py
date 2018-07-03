""" The adapter module helps the user mutate one collection into another. This works similar to
a calc class in calc_factory.
AbstractAdapter's call takes a collection's data attribute as the first argument. An adapt() method must be
overridden by the user which must return an instance of AdapterOutputContainer. This is enforced by returning the
helper method

Once the class is declared the user register's the adapter using the register static method
"""
import abc
from .registry import register_adapter_to_collection, register_adaptable_collection


def check_adapter_call(method):
    """ a helper decorater for the __call__ method that does some type checking
    """
    def inner(*args, **kwargs):
        self = args[0]
        coll = args[1]
        if not isinstance(coll, self.from_collection_class):
            raise TypeError('Cannot adapt from type {}'.format(coll))

        result = method(*args, **kwargs)

        if not isinstance(result, AdapterOutputContainer):
            raise TypeError('Adapters must return an instance of AdapterOutputContainer')

        return result
    return inner


class AdapterOutputContainer(object):
    """ A generic container class for moving data out of adapters. It holds the target output
    collection along with any context data that might need to be passed on to the caller or
    another adapter. Essentially 'side effects' from the adaptation that might be needed further along
    in the adapter chain

    This is used internally in Adapter.__call__
    """

    def __init__(self, collection, **context):
        self.collection = collection
        self._context = {}

        for k,v in context.items():
            setattr(self, k, v)  # set on class and load into a context dict for easy access
            self._context[k] = v # load in context

    @property
    def context(self):
        return self._context


class AbstractAdapter(abc.ABC):
    """ Concrete Adapters subclass this class and override its adapt method with an implementation.
    Other methods may be added as helper classes
    """

    target_collection_class = None
    from_collection_class = None
    is_registered = False #NOTE set to True in the adapter registery


    def render_return(self, data, **context):
        """ A helper method renders the data response to the target_collection_class and passes context data.
        Must return the data in an instance of AdapterOutputContainer
        """
        coll = self.target_collection_class()
        coll.load_data(data)
        return AdapterOutputContainer(coll, **context)


    @abc.abstractmethod
    def adapt(self, collection, **context):
        """ The user must overrides this method to do the data cleaning. Any additional methods
        needed for clean should be considered private to the Adapter subclass. Must call render_return
        """
        # get the data from the input_collection  (collection.data or collection.to_dataframe() or whatever...)
        # get the context args you need... context.pop('some-key') or context['some-key']
        
        #return self.render_return(collection, **context) #NOTE this is an example of how to return from adapt



    @check_adapter_call
    def __call__(self, collection, **context):
        """ Wraps the adapt call and does some type checking. Makes sure that input collection
        if the from_class and the output collection and context are delivered in an AdapterOutputContainer.
        An adapter should be used as
        """
        return self.adapt(collection, **context)



def register_adapter(adapter_class):
    """ Registers the adapter class in the graph chain by setting its to and from classes
    """
    # adapter_class.target_collection_class = target_class  # assign the class a from and target
    # adapter_class.from_collection_class = from_class

    target_lookup_path = adapter_class.target_collection_class.get_fully_qualified_class_path()  # get some path names
    from_lookup_path = adapter_class.from_collection_class.get_fully_qualified_class_path()

    # register adapter to the 'from' classes 'adapters' list and link the two classes on the 'target'
    # in its 'adaptable_from' list
    register_adapter_to_collection(from_lookup_path, adapter_class)
    register_adaptable_collection(target_lookup_path, adapter_class.from_collection_class)

    adapter_class.is_registered = True
