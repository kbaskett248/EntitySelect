from abc import ABCMeta, abstractmethod
import inspect

import sublime

try:
    import sublimelogging
    logger = sublimelogging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SortableABCMeta(ABCMeta):
    """Enables comparing a class to another object."""
    
    def __lt__(self, other):
        try:
            return self.__name__ < other.__repr__()
        except TypeError:
            return self.__name__ < other.__name__


class EntitySelector(object, metaclass = SortableABCMeta):
    """General purpose superclass for matching portions of text."""
    
    # Dictionary used to store data about a view. The dictionary is keyed by 
    # the view ID and contains ViewData objects.
    ViewSelectors = dict() 

    # A list of all possible EntitySelector classes to check
    PossibleSelectors = []

    # A list of callbacks to be run before the selection checks are run.
    # Callbacks are called with the following arguments:
    #   cls - If the view has a current EntitySelector, this will be the class
    #         of that selector. Otherwise it will be EntitySelector.
    #   selector - If the view has a current EntitySelector, this will be that
    #              selector. Otherwise, it will be None.
    #   view - The given view
    OnBeforeCheckCallbacks = []

    # A list of callbacks to be run after the selection checks are run.
    # Callbacks are called with the following arguments:
    #   cls - If the view has a current EntitySelector, this will be the class
    #         of that selector. Otherwise it will be EntitySelector.
    #   selector - If the view has a current EntitySelector, this will be that
    #              selector. Otherwise, it will be None.
    #   view - The given view
    OnAfterCheckCallbacks = []    

    @classmethod
    @abstractmethod
    def scope_view_enabler(cls):
        """This should return a scope that will determine if an EntitySelector 
        will be enabled for a view.

        This function should be overloaded by all extending classes.

        """
        pass

    @classmethod
    def check_scope_for_view(cls, view):
        """Returns the score of the defined scope in the given view."""
        # logger.debug('cls.scope_view_enabler = %s', cls.scope_view_enabler())
        try:
            return max([view.score_selector(s.begin(), cls.scope_view_enabler())
                        for s in view.sel()])
        except ValueError:
            return view.score_selector(0, cls.scope_view_enabler())

    @classmethod
    def enable_for_view(cls, view):
        """Returns True if the EntitySelector should be enabled for the given view.

        This allows for checking in addition to the scope check.

        """
        return True

    @classmethod
    def check_scope_for_selection(cls, view, check_all_regions = False):
        """Returns a list of score for the defined scope across the selections in the view.

        Keyword arguments:
        check_all_regions - If this is True, all selections in the view are 
            checked. Otherwise, only the first selection is checked.

        """
        if check_all_regions:
            return [view.score_selector(s.begin(), cls.scope_selection_enabler())
                    for s in view.sel()]
        else:
            return [view.score_selector(view.sel()[0].begin(), cls.scope_selection_enabler())]

    @classmethod
    @abstractmethod
    def scope_selection_enabler(cls):
        """Returns the name of a scope to determine if an EntitySelector will 
        be enabled for the current selection.

        This function should be overloaded by all extending classes."""
        pass

    @classmethod
    def enable_for_selection(cls, view):
        """Returns True if the EntitySelector should be enabled for the given selection.

        This allows for checking in addition to the scope check. The EntitySelector 
        object should be created within this function.

        """
        cls(view)
        return True

    @classmethod
    def update_selector_for_view(cls, view, selector = None):
        """Updates the EntitySelector assigned to the specified view.

        If no ViewData object exists for the view, one is created and the 
        specified selector is assigned.

        """
        try:
            vd = EntitySelector.ViewSelectors[view.id()]
        except KeyError:
            EntitySelector.ViewSelectors[view.id()] = ViewData(view, selector)
        else:
            vd.selector = selector

    @classmethod
    def get_selector_for_view(cls, view):
        """Returns the EntitySelector object assigned to the given view.

        If no selector is assigned, None is returned.

        """
        try:
            return EntitySelector.ViewSelectors[view.id()].selector
        except KeyError:
            return None

    @classmethod
    def get_possible_selectors_for_view(cls, view):
        """Returns a list of the possible selectors for a view."""
        try:
            vd = EntitySelector.ViewSelectors[view.id()]
            return EntitySelector.ViewSelectors[view.id()].get_possible_selectors_for_view(view)
        except KeyError:
            return []

    @classmethod
    def sorted_selectors_for_selection(cls, view):
        """Returns a sorted list of EntitySelector classes that match the current scope.

        The list is sorted in descending order of score.

        """
        selectors = []
        for c in cls.get_possible_selectors_for_view(view):
            score = c.check_scope_for_selection(view)[0]
            if score > 0:
                selectors.append((score, c))

        selectors.sort(reverse = True)
        return [c for s, c in selectors]

    @classmethod
    def add_on_before_check_callback(cls, callback, propagate = False):
        """Adds a callback to be run before the selectors are checked."""
        if (cls == EntitySelector) or propagate:
            EntitySelector.OnBeforeCheckCallbacks.append(callback)
        else:
            if not hasattr(cls, 'OnBeforeCheckCallbacks'):
                cls.OnBeforeCheckCallbacks = []
            cls.OnBeforeCheckCallbacks.append(callback)

    @classmethod
    def add_on_after_check_callback(cls, callback, propagate = False):
        """Adds a callback to be run after the selectors are checked."""
        if (cls == EntitySelector) or propagate:
            EntitySelector.OnAfterCheckCallbacks.append(callback)
        else:
            if not hasattr(cls, 'OnAfterCheckCallbacks'):
                cls.OnAfterCheckCallbacks = []
            cls.OnAfterCheckCallbacks.append(callback)

    @classmethod
    def get_on_before_check_callbacks(cls):
        """Returns a list of on_before_check callbacks."""
        if cls == EntitySelector:
            return EntitySelector.OnBeforeCheckCallbacks
        else:
            callbacks = []
            for c in cls.__mro__:
                try:
                    callbacks.extend(c.OnBeforeCheckCallbacks)
                except AttributeError:
                    pass
            return callbacks

    @classmethod
    def get_on_after_check_callbacks(cls):
        """Returns a list of on_after_check callbacks."""
        if cls == EntitySelector:
            return EntitySelector.OnAfterCheckCallbacks
        else:
            callbacks = []
            for c in cls.__mro__:
                try:
                    callbacks.extend(c.OnAfterCheckCallbacks)
                except AttributeError:
                    pass
            return callbacks

    @classmethod
    def run_on_before_check_callbacks(cls, view):
        """Calls the on_before_check callbacks."""
        # logger.debug('running on before check callbacks')
        selector = cls.get_selector_for_view(view)
        if selector is None:
            for c in cls.get_on_before_check_callbacks():
                try:
                    c(cls = EntitySelector, selector = None, view = view)
                except Exception:
                    logger.exception('Error occurred in EntitySelector on_before_check callback')
        else:
            for c in cls.get_on_before_check_callbacks():
                try:
                    c(cls = selector.__class__, selector = selector, view = view)
                except Exception:
                    logger.exception('Error occurred in EntitySelector on_before_check callback')

    @classmethod
    def run_on_after_check_callbacks(cls, view):
        """Calls the on_after_check callbacks."""
        # logger.debug('running on after check callbacks')
        selector = cls.get_selector_for_view(view)
        if selector is None:
            for c in cls.get_on_after_check_callbacks():
                try:
                    c(cls = EntitySelector, selector = None, view = view)
                except Exception:
                    logger.exception('Error occurred in EntitySelector on_after_check callback')
        else:
            for c in cls.get_on_after_check_callbacks():
                try:
                    c(cls = selector.__class__, selector = selector, view = view)
                except Exception:
                    logger.exception('Error occurred in EntitySelector on_after_check callback')

    @classmethod
    def add_possible_selector(cls):
        EntitySelector.PossibleSelectors.append(cls)

    @classmethod
    def remove_possible_selector(cls):
        EntitySelector.PossibleSelectors.remove(cls)

    @classmethod
    def match_entity(cls, view):
        """Checks the loaded DocFinders. If one is found matching the current 
        selection, the word is underlined.

        """
        if not cls.PossibleSelectors:
            return

        if view.settings().get('is_widget', False):
            return

        selector = cls.get_selector_for_view(view)
        if selector is not None:
            if selector.compare_current_selection(view):
                return

        # Prepare for a new selector
        EntitySelector.update_selector_for_view(view)
        cls.run_on_before_check_callbacks(view)

        if not cls.check_regions(view):
            return

        for c in cls.sorted_selectors_for_selection(view):
            kwargs = c.enable_for_selection(view)
            if kwargs:
                c(view, **kwargs)
                break

        cls.run_on_after_check_callbacks(view)

    @classmethod
    def check_regions(cls, view):
        """Returns False if there is a difference between the start and end scope of a selection.

        Compares the beginning and end of all selections. If there is any 
        difference between them for any of the selections, return False.
        Otherwise return True.

        """
        for s in view.sel():
            start_scope = view.scope_name(s.begin()).strip()
            if view.scope_name(s.end()).strip() != start_scope:
                if s.empty():
                    return False
                elif view.scope_name(s.end()-1).strip() != start_scope:
                    return False
            start_scope = start_scope.split(' ')[-1]
            try:
                if start_scope != overall_scope:
                    return False
            except NameError:
                overall_scope = start_scope
        return True

    @abstractmethod
    def __init__(self, view, **kwargs):
        super(EntitySelector, self).__init__()
        self.view = view
        self.regions = view.sel()
        self.__class__.update_selector_for_view(view, self)

    def compare_current_selection(self, view, check_all_regions = False):
        """Returns True if the current view selection matches the selections stored in the selector."""
        for score in self.__class__.check_scope_for_selection(view, check_all_regions):
            if score <= 0:
                return False

        if check_all_regions:
            selections = view.sel()
        else:
            selections = [view.sel()[0]]

        for s in selections:
            for r in self.regions:
                if r.contains(s):
                    break
            else:
                return False

        return True

    @classmethod
    def get_selector_types(cls):
        types = []
        for c in cls.__mro__:
            try:
                types.append(c.SelectorType)
            except AttributeError:
                pass
        return types
    

    @staticmethod
    def get_defined_classes(globals_):
        file_ = globals_['__file__']
        return [c for c in globals_.values() if 
                (inspect.isclass(c) and 
                 (inspect.getfile(c) == file_) and 
                 (EntitySelector in inspect.getmro(c))
                )]



class ViewData(object):
    """Stores data for a view."""

    def __init__(self, view, selector = None):
        super(ViewData, self).__init__()
        self.id = view.id()
        self.scope = ViewData.scope_from_view(view)
        self.selector = selector
        self.update_possible_selectors(view)

    def get_possible_selectors_for_view(self, view):
        """Returns a list of possible EntitySelector classes for a view.

        The selectors returned here are based in part on the primary source
        scope for a view. That value is stored. If the value changes, the 
        list of possible EntitySelector classes is recomputed.

        """
        scope = ViewData.scope_from_view(view)
        hash_ = ViewData.get_possible_selectors_hash()
        if ((self.scope != scope) or 
            (self.possible_selectors_hash != hash_)):
            self.scope = scope
            self.update_possible_selectors(view)

        return self.possible_selectors

    def update_possible_selectors(self, view):
        self.possible_selectors_hash = ViewData.get_possible_selectors_hash()
        self.possible_selectors = [s for s in EntitySelector.PossibleSelectors 
                                   if ((s.check_scope_for_view(view) > 0)
                                       and s.enable_for_view(view))]

    @staticmethod
    def scope_from_view(view):
        """Returns the primary source scope for a view."""
        try:
            scope = view.scope_name(view.sel()[0].begin())
        except IndexError:
            scope = view.scope_name(0)
        
        return scope.split(' ')[0]

    @staticmethod
    def get_possible_selectors_hash():
        return hash(str(EntitySelector.PossibleSelectors))
        

    