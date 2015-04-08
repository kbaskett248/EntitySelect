import sublime
import sublime_plugin

from EntitySelect import EntitySelector, DocLink, Highlight, PreemptiveHighlight

import logging
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class EntitySelectListenerCommand(sublime_plugin.EventListener):

    def on_selection_modified_async(self, view):
        # logger.debug('Running on_modified')
        EntitySelector.match_entity(view)

    def on_activated_async(self, view):
        # logger.debug('Running on_activated')
        EntitySelector.match_entity(view)


class DocLinkCommand(sublime_plugin.TextCommand):
    """Command to find the documentation for the currently selected entity.

    This command can be extended by defining new DocFinder classes.

    """

    def run(self, edit):
        """Calls the show method of the DocFinder assigned to the view."""
        try:
            s = EntitySelector.get_selector_for_view(self.view)
            if s.enable_doc_link():
                s.show_doc()
        except AttributeError:
            pass

    def description(self):
        """Returns the description for the DocFinder assigned to the view."""
        try:
            es = EntitySelector.get_selector_for_view(self.view)
            if es.enable_doc_link():
                return es.doclink_description()
        except AttributeError:
            pass
        return 'DocLink'

    def is_visible(self):
        """Returns true if the current file is an M-AT file."""
        try:
            for s in EntitySelector.get_possible_selectors_for_view(self.view):
                if DocLink in s.__mro__:
                    return True
        except AttributeError:
            pass
        return False

    def is_enabled(self):
        """Returns True if a DocFinder is assigned to the view."""
        try:
            return EntitySelector.get_selector_for_view(
                self.view).enable_doc_link()
        except AttributeError:
            return False


class EntityselectHighlightCommand(sublime_plugin.TextCommand):
    """Command to find the documentation for the currently selected entity.

    This command can be extended by defining new DocFinder classes.

    """

    def run(self, edit, cmd):
        """Calls the show method of the DocFinder assigned to the view."""
        if cmd == Highlight.HIGHLIGHT_COMMAND:
            try:
                s = EntitySelector.get_selector_for_view(self.view)
                if s.enable_highlight():
                    s.highlight()
            except AttributeError:
                pass
        else:
            hl = Highlight.get_highlighter_for_view(self.view)
            if hl is None:
                pass
            elif cmd == Highlight.FORWARD_COMMAND:
                hl.move_to_highlight(forward=True)
            elif cmd == Highlight.BACKWARD_COMMAND:
                hl.move_to_highlight(forward=False)
            elif cmd == Highlight.CLEAR_COMMAND:
                hl.remove_highlighter_from_view()
            elif cmd == Highlight.SELECT_ALL_COMMAND:
                hl.select_all_highlights()
            elif cmd == Highlight.SHOW_ALL_COMMAND:
                self.show_all(hl)

    def description(self, cmd):
        """Returns the description for the DocFinder assigned to the view."""
        if cmd == Highlight.HIGHLIGHT_COMMAND:
            try:
                return EntitySelector.get_selector_for_view(
                    self.view).highlight_description(cmd)
            except AttributeError:
                return 'Highlight'
        else:
            hl = Highlight.get_highlighter_for_view(self.view)
            if hl is None:
                return 'Highlight'
            return hl.highlight_description(cmd)

    def is_visible(self, cmd):
        """Returns true if the current file is an M-AT file."""
        if cmd == Highlight.HIGHLIGHT_COMMAND:
            try:
                for s in EntitySelector.get_possible_selectors_for_view(
                        self.view):
                    if Highlight in s.__mro__:
                        return True
            except AttributeError:
                pass
            return False
        elif Highlight.get_highlighter_for_view(self.view) is None:
            return False
        else:
            return True

    def is_enabled(self, cmd):
        """Returns True if a Highlighter is assigned to the view."""
        if cmd == Highlight.HIGHLIGHT_COMMAND:
            try:
                return EntitySelector.get_selector_for_view(
                    self.view).enable_highlight()
            except AttributeError:
                return False
        elif Highlight.get_highlighter_for_view(self.view) is None:
            return False
        else:
            return True

    def show_all(self, highlighter):
        items = highlighter.highlight_regions
        disp_items = [highlighter.get_display_region(r) for r in items]
        curr_sel = [s for s in self.view.sel()]
        curr_vp = self.view.viewport_position()
        func = lambda x: self.show_error(x, items, curr_sel, curr_vp)
        self.view.window().show_quick_panel(disp_items,
                                            func,
                                            0,
                                            0,
                                            func)

    def show_error(self, index, items, curr_sel, curr_vp):
        if index == -1:
            self.view.sel().clear()
            self.view.sel().add_all(curr_sel)
            self.view.set_viewport_position(curr_vp, True)
        else:
            reg = items[index]
            self.view.sel().clear()
            self.view.sel().add(reg)
            self.view.show_at_center(reg)


class PreemptiveHighlightCommand(sublime_plugin.TextCommand):
    """Command to find the documentation for the currently selected entity.

    This command can be extended by defining new DocFinder classes.

    """

    def run(self, edit, highlighter):
        """Calls the show method of the DocFinder assigned to the view."""
        c = PreemptiveHighlight.get_preemptive_highlighter(highlighter)
        if c is not None:
            ps = c.get_preemptive_highlight_selection(self.view)
            if not ps:
                sublime.status_message('No regions to highlight')
                return

            # Copy current selection, then replace with preemptive selection
            current_selection = self.copy_current_selection()
            self.view.sel().clear()
            self.view.sel().add_all(ps)

            # Get current selector
            current_selector = EntitySelector.get_selector_for_view(self.view)

            # Determine if the highlighter should be enabled
            enabled = c.enable_for_selection(self.view)
            if not enabled:
                sublime.status_message('No regions to highlight')
                self.view.sel().clear()
                self.view.sel().add_all(current_selection)
                return

            # Create the highlighter and highlight
            preemptive_highlighter = c(self.view, **enabled)
            preemptive_highlighter.highlight()

            # Restore the current selection
            self.view.sel().clear()
            self.view.sel().add_all(current_selection)

            # If there were no highlighted regions, remove the highlight
            if not preemptive_highlighter.highlight_regions:
                sublime.status_message('No regions to highlight')
                preemptive_highlighter.remove_highlighter_from_view()

            # Restore the current selector
            if current_selector is None:
                EntitySelector.update_selector_for_view(self.view, None)
            else:
                current_selector.__class__.update_selector_for_view(
                    self.view, current_selector)

    def copy_current_selection(self):
        return [r for r in self.view.sel()]

    def is_visible(self, highlighter):
        """Returns true if the current file is an M-AT file."""
        if (PreemptiveHighlight.get_preemptive_highlighter(highlighter)
                is not None):
            return True
        return False

    def is_enabled(self, highlighter):
        """Returns True if a DocFinder is assigned to the view."""
        return self.is_visible(highlighter)


class HighlightListenerCommand(sublime_plugin.EventListener):
    """Refreshes the highlights on activation and modification of the view."""

    def on_activated_async(self, view):
        self.update_highlights(view)

    def on_modified_async(self, view):
        self.update_highlights(view)

    def update_highlights(self, view):
        if view.settings().get('is_widget', False):
            return
        hl = Highlight.get_highlighter_for_view(view)
        if hl is not None:
            hl.highlight()
            if not hl.highlight_regions:
                hl.remove_highlighter_from_view()
        else:
            view.erase_regions('entity_select_highlight')


class EntitySelectInsertInViewCommand(sublime_plugin.TextCommand):

    def run(self, edit, text, point=0):
        self.view.insert(edit, point, text)
