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
        'registered_adapters': set(),  #NOTE these are the classes registered adapters
        'adaptable_from': set()   #NOTE these are other collection objects a coll can be adapted from
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

def bfs_shortest_path(graph, start, end):
    """ a generic bfs search algo
    """
    def _bfs_paths(graph, start, end):
        # bfs using a generator. should return shortest path if any for an iteration
        queue = [(start, [start])]
        while queue:
            (vertex, path) = queue.pop(0)
            for next_vertex in graph[vertex] - set(path):
                if next_vertex == end:
                    yield path + [next_vertex]
                else:
                    queue.append((next_vertex, path + [next_vertex]))

    try:
        return next(_bfs_paths(graph, start, end))
    except StopIteration:
        return []

def adapter_path(from_class, end_class):
    """ traverses the registry and builds a class path of adapters to a target using
    by looking at each nodes 'adaptable_from' set. It will traverse the graph until all possibilities
    are exhausted. If it finds a matching adaptable, it returns the path of adapter objects that
    are needed to adapt the schema. If no path is found it returns an empty list
    """

    current_graph = _make_cc_graph()
    shortest_path = bfs_shortest_path(current_graph, from_class, end_class)

    
