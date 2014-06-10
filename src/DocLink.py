from abc import ABCMeta, abstractmethod
import os
import time
import webbrowser

import sublime

from .EntitySelector import EntitySelector, SortableABCMeta

try:
    import sublimelogging
    logger = sublimelogging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class DocLink(EntitySelector):

    def __init__(self, view, search_string = None, search_region = None, **kwargs):
        if search_region is not None:
            if DocLink.selection_in_region(view, search_region):
                super(DocLink, self).__init__(view, search_string = search_string, 
                                              search_region = search_region, 
                                              **kwargs)
                if (search_string is None):
                    self.search_string = view.substr(search_region)
                else:
                    self.search_string = search_string
                self.regions = [search_region]
            else:
                logger.warning('Selection not in Region: %s - %s', search_region, search_string)
        else:
            super(DocLink, self).__init__(view, search_string = search_string, 
                                          search_region = search_region, 
                                          **kwargs)
            self.regions = [search_region]
            self.search_string = search_string

    @abstractmethod
    def show_doc(self):
        """This is called to show the documentation for an entity."""
        pass

    @staticmethod
    def selection_in_region(view, region):
        """Return True if any view selections are in the region."""
        for s in view.sel():
            if region.contains(s):
                return True
        return False

    def doclink_description(self):
        """Return a description string to display in the context menu."""
        try:
            if self.search_string:
                return 'DocLink: %s' % self.search_string
        except AttributeError:
            pass
        
        return 'DocLink'

    @property
    def open_status_message(self):
        """Status message displayed when opening documentation."""
        return "DocLink: " + self.search_string

    @staticmethod
    def add_regions(view = None, selector = None, **kwargs):
        """Adds regions to the view and assigns the DocFinder to the view."""
        if ((view is not None) and (selector is not None) and 
            isinstance(selector, DocLink) and selector.enable_doc_link()):
            view.add_regions('doc_link', selector.regions, 
                             view.scope_name(selector.regions[0].begin()),
                             flags = (sublime.DRAW_NO_FILL | 
                                      sublime.DRAW_NO_OUTLINE |
                                      sublime.DRAW_STIPPLED_UNDERLINE |
                                      sublime.HIDE_ON_MINIMAP)
                         )
    
    @staticmethod
    def erase_regions(view = None, **kwargs):
        """Clears regions from the view and clears the DocFinder assigned to the view."""
        if view is not None:
            view.erase_regions('doc_link')
    
    def enable_doc_link(self):
        """Return True to allow DocLink functionality for the EntitySelector."""
        return True

    def show_doc_on_web(self, url):
        """Opens the given url in the default web browser."""
        webbrowser.open(url)

    def show_doc_in_file(self, file_, region = None, row = 0, col = 0, show_at_top = True):
        """Opens the file and shows the given region."""
        logger.debug('show_doc_in_file')
        status_message_suffix = ''

        if (file_ is None):
            status_message_suffix = 'not found'
        elif (file_ == self.view.file_name()):
            logger.debug('in current file')
            self.view.sel().clear()
            self.view.sel().add(region)
            if show_at_top:
               line = self.view.line(region)
               line = self.view.line(line.begin() - 1)
               v = self.view.text_to_layout(line.begin())
               self.view.set_viewport_position(v, True)
            else:
                self.view.show(region, True)

            status_message_suffix = 'found in current file'
        elif not os.path.exists(file_):
            status_message_suffix = 'not found'
        else:
            status_message_suffix = 'found in other file'
            if (region is None):
                view = self.view.window().open_file(
                            "{0}:{1}:{2}".format(file_, row, col),
                             sublime.ENCODED_POSITION)
                if ((row != 0) and (col != 0)):
                    sublime.set_timeout_async(
                        lambda: self.show_and_select_opened_file(view, region, 
                                    row, col, show_at_top), 0)
            else:
                view = self.view.window().open_file(file_, sublime.ENCODED_POSITION)
                sublime.set_timeout_async(
                    lambda: self.show_and_select_opened_file(view, region, 
                                row, col, show_at_top), 0)

        return status_message_suffix

    def show_and_select_opened_file(self, view, region, row, col, show_at_top):
        """Helper method to show the given selection in a just opened file."""
        while view.is_loading():
            time.sleep(0.01)

        s = view.sel()
        s.clear()
        if region is not None:
            s.add(region)
            line = view.line(region)
        else:
            p = view.text_point(row-1, col-1)
            line = view.line(p)
            selection = sublime.Region(p, line.end())
            s.add(selection)

        if show_at_top:
            previous_line = view.line(line.begin()-1)
            v = view.text_to_layout(previous_line.begin())
            view.set_viewport_position(v, False)

DocLink.add_on_before_check_callback(DocLink.erase_regions) 
DocLink.add_on_after_check_callback(DocLink.add_regions)