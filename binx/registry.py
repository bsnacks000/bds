""" A private registry for the collection objects. It is mainly used to register
adaption classes on each collection object for data cleaning/processing. The classes
are created by the user and registered at runtime.
"""

from .exceptions import RegistryError
from .utils import bfs_shortest_path

_collection_registry = {}

from pprint import pprint

def register_collection(cls):
    """ registers a new collection class.
    """
    fullpath = cls.__module__ + '.' + cls.__name__

    if fullpath in _collection_registry: # if the fullpath is already
        raise RegistryError('The classname {} has already been registered. Create a different name for your collection'.format(fullpath))

    # you must do the lookup by fullpath
    _collection_registry[fullpath] = (cls, {
        'serializer_class': cls.serializer_class,
        'internal_class': cls.internal_class,
        'registered_adapters': set(),  #NOTE these are the classes registered adapters
        'adaptable_from': set()   #NOTE these are other collection objects a coll can be adapted from
    })
    #pprint(_collection_registry)


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
    _collection_registry[classname][1]['registered_adapters'].add(adapter)


def register_adaptable_collection(classname, coll):
    """ appends an adaptable collection to a classes list of adaptable collections
    """
    _collection_registry[classname][1]['adaptable_from'].add(coll)


def _make_cc_graph():
    """ returns a graph of connected collections. This is given as a flat dictionary of sets
    using the 'adaptable_from' sets for each graph. This is used by adapter path to return a
    path of classes connecting two nodes
    """
    graph = {}
    for name, entry in _collection_registry.items():
        graph[entry[0]] = entry[1]['adaptable_from']
    return graph



def adapter_path(from_class, end_class):
    """ traverses the registry and builds a class path of adapters to a target using
    by looking at each nodes 'adaptable_from' set. It will traverse the graph until all possibilities
    are exhausted. If it finds a matching adaptable, it returns the path of adapter objects that
    are needed to adapt the schema. If no path is found it returns an empty list
    """

    current_graph = _make_cc_graph() # create snapshot of current path
    colls = bfs_shortest_path(current_graph, from_class, end_class) # return adaptable collection path
    if len(colls) == 0:
        return colls  # empty list

    # loop through list of classes going forward and find the appropriate adapter for the next coll class
    # append these to a list and return
    adapters = [None] * (len(colls) - 1)
    for i in range(len(colls)):
        target = colls[i+1]   # get refs
        current = colls[i]
        current_registry_entry = current.get_registry_entry() # return the complete registry entry
        for adapter_class in current_registry_entry['registered_adapters']:
            if adapter_class.target_collection_class is target:
                adapters[0] = adapter_class

    return adapters
