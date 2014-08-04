from abc import ABCMeta, abstractmethod

class SortableABCMeta(ABCMeta):
    """Enables comparing a class to another object."""
    
    def __lt__(self, other):
        try:
            return self.__name__ < other.__repr__()
        except TypeError:
            return self.__name__ < other.__name__
