from abc import abstractmethod

import sublime

from .EntitySelector import EntitySelector

try:
    import sublimelogging
    logger = sublimelogging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class Highlight(EntitySelector):
    """Base class that adds highlighting functionality to EntitySelectors."""

    # Dictionary linking a view with its Assigned highlighter object. 
    Highlighters = dict()

    # Constants for each available highlighter command. 
    HIGHLIGHT_COMMAND = 'highlight'

    FORWARD_COMMAND = 'forward'

    BACKWARD_COMMAND = 'backward'

    CLEAR_COMMAND = 'clear'

    SELECT_ALL_COMMAND = 'select_all'

    SHOW_ALL_COMMAND = 'show_all'

    STATUS_KEY = 'entity_select_num_highlights'

    def __init__(self, view, search_string = None, search_region = None, **kwargs):
        super(Highlight, self).__init__(view, search_string = search_string, 
                                              search_region = search_region, 
                                              **kwargs)
        if search_string == None:
            self.search_string = view.substr(search_region)
        else:
            self.search_string = search_string
        self.regions = [search_region]
        self.highlight_regions = []

    def highlight_description(self, command):
        """Return the command description."""
        if not self.enable_highlight():
            return 'Highlight'
        elif (command == self.HIGHLIGHT_COMMAND):
            return self.highlight_description_highlight
        elif (command == self.FORWARD_COMMAND):
            return self.highlight_description_forward
        elif (command == self.BACKWARD_COMMAND):
            return self.highlight_description_backward
        elif (command == self.CLEAR_COMMAND):
            return self.highlight_description_clear
        elif (command == self.SELECT_ALL_COMMAND):
            return self.highlight_description_select_all
        elif (command == self.SHOW_ALL_COMMAND):
            return self.highlight_description_show_all
        else:
            return 'Unsupported Command'

    @property
    def highlight_description_highlight(self):
        return 'Highlight: ' + self.search_string

    @property
    def highlight_description_forward(self):
        return 'Next instance of ' + self.search_string
    
    @property
    def highlight_description_backward(self):
        return 'Previous instance of ' + self.search_string
    
    @property
    def highlight_description_clear(self):
        return 'Clear highlights'
    
    @property
    def highlight_description_select_all(self):
        return 'Select all instances of ' + self.search_string

    @property
    def highlight_description_show_all(self):
        return 'Show all instances of ' + self.search_string

    def highlight_status_message(self, total, selection = None):
        """Return a message to be displayed in the status bar when highlights are shown.

        Keyword arguments:
        total - the total number of visible highlights
        selection - the number of the selected highlight if one is selected

        This method can be overridden if you want to display additional
        information.

        """
        if (selection is not None):
            return "%s of %s highlighted regions" % (selection, total)
        else:
            return "%s highlighted regions" % total
    
    def enable_highlight(self):
        """This method can be overridden if highlighting should be enabled only for certain selections."""
        return True

    def highlight(self):
        """Assign a highlighter to the view and add the regions to the view."""
        hr = self.get_highlight_regions()
        if hr:
            self.highlight_regions.clear()
            self.highlight_regions.extend(hr)
            self.assign_highlighter_to_view()
            self.add_highlight_regions()
        else:
            self.remove_highlighter_from_view()

    def assign_highlighter_to_view(self):
        """Assign the highlighter to the view."""
        Highlight.Highlighters[self.view.id()] = self

    def remove_highlighter_from_view(self):
        """Removes the highlighter from the view."""
        Highlight.Highlighters[self.view.id()] = None
        self.erase_highlight_regions()

    @classmethod
    def get_highlighter_for_view(cls, view):
        """Return the highlighter assigned to a view, or None."""
        try:
            return Highlight.Highlighters[view.id()]
        except KeyError:
            return None

    @abstractmethod
    def get_highlight_regions(self):
        """Return a list of regions to highlight. This method should be overridden by subclasses."""
        return []

    def add_highlight_regions(self):
        """Add the highlight regions to the view.

        Also displays the status message.

        """
        self.view.add_regions('entity_select_highlight',
                              self.highlight_regions, 
                              'string', 
                              'dot',
                              sublime.DRAW_NO_FILL)
        Highlight.display_status_string(view = self.view, highlighter = self)

    def erase_highlight_regions(self):
        """Remove the highlight regions from the view.

        Also removes the status message.

        """
        self.view.erase_regions('entity_select_highlight')
        self.view.erase_status(Highlight.STATUS_KEY)

    def move_to_highlight(self, forward = True):
        """Replace the current selection with the next or previous highlight and show it.

        Keyword arguments:
        forward - True to move forward. Otherwise moves backward.

        """
        selection = self.view.sel()
        sel = selection[0]
        regions = self.highlight_regions
        regions.sort()
        next_ = regions[0]
        prev = regions[-1]
        begin = sel.begin()
        end = sel.end()

        for r in regions:
            if r.end() <= begin:
                prev = r
            elif r.begin() >= end:
                next_ = r
                break

        selection.clear()
        if forward:
            selection.add(next_)
        else:
            selection.add(prev)
        self.view.show(selection[0], True)

    def select_all_highlights(self):
        """Selects all the highlighted regions."""
        regions = self.highlight_regions
        sel = self.view.sel()
        sel.clear()
        sel.add_all(regions)
        self.view.show(sel[0], True)

    def get_display_region(self, reg):
        """Return a string to display in the palette list for the given region."""
        return '%s: %s' % (self.view.rowcol(reg.begin())[0] + 1,
                           self.view.substr(self.view.line(reg)))

    @staticmethod
    def display_status_string(view = None, highlighter = None, **kwargs):
        """Adds or updates the Highlighter status string.

        This is added as an On After Check Callback.
        
        """
        if (view is not None):
            if highlighter is None:
                highlighter = Highlight.get_highlighter_for_view(view)
            if (highlighter is not None):
                hr = highlighter.get_highlight_regions()
                sel = view.sel()[0]
                current = None
                for i, r in enumerate(hr, start = 1):
                    if r.intersects(sel):
                        current = i
                        break
                view.set_status(Highlight.STATUS_KEY, 
                                highlighter.highlight_status_message(len(hr), 
                                                                     selection = current))
            else:
                view.erase_status(Highlight.STATUS_KEY)
    
Highlight.add_on_after_check_callback(Highlight.display_status_string)


class PreemptiveHighlight(Highlight):

    # A dictionary used to store any registered Preemptive Highlighters by 
    # the preemptive_highlight_id().
    PreemptiveHighlighters = dict()

    @classmethod
    @abstractmethod
    def get_preemptive_highlight_selection(cls, view):
        """Return a region to enable a highlight."""
        pass

    @classmethod
    def add_possible_selector(cls):
        """Adds the given class to the list of Possible EntitySelectors."""
        super(PreemptiveHighlight, cls).add_possible_selector()
        cls.add_preemptive_highlighter()

    @classmethod
    def remove_possible_selector(cls):
        """Removes the given selector from the list of Possible EntitySelectors."""
        super(PreemptiveHighlight, cls).remove_possible_selector()
        cls.remove_preemptive_highlighter()

    @classmethod
    def preemptive_highlight_id(cls):
        """Returns a string used to identify a Preemptive Highlighter.

        This string is used when creating a command to invoke the highlighter.

        """
        return cls.__name__

    @classmethod
    def add_preemptive_highlighter(cls):
        """Adds the given class to the list of Preemptive Highlighters."""
        try:
            PreemptiveHighlight.PreemptiveHighlighters[cls.preemptive_highlight_id()] = cls
        except AttributeError:
            logger.error('{name} cannot be added as a Preemptive Highlighter'.format(name = cls.__name__))

    @classmethod
    def remove_preemptive_highlighter(cls):
        """Removes the given class from the list of PreemptiveHighlighters."""
        try:
            del PreemptiveHighlight.PreemptiveHighlighters[cls.preemptive_highlight_id()]
        except AttributeError:
            pass
        except KeyError:
            pass

    @classmethod
    def get_preemptive_highlighter(cls, ident):
        """Returns a reference to the PreemptiveHighlight class identified by ident."""
        try:
            return PreemptiveHighlight.PreemptiveHighlighters[ident]
        except AttributeError:
            logger.error('{name} is not a recognized Preemptive Highlighter'.format(name = ident))
            return None

    

    