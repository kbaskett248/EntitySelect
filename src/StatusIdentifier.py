from .EntitySelector import EntitySelector

try:
    import sublimelogging
    logger = sublimelogging.getLogger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class StatusIdentifier(EntitySelector):

    StatusKey = '_status_identifier'

    def __init__(self, view, status_string = None, **kwargs):
        super(StatusIdentifier, self).__init__(view, **kwargs)
        self.status_string = status_string

    @property
    def status_string(self):
        """Returns the string to display in the status bar.

        This is done as a property so it can be computed if desired.

        """
        return self._status_string
    @status_string.setter
    def status_string(self, value):
        self._status_string = value
    
    @staticmethod
    def display_status_string(view = None, selector = None, **kwargs):
        """Adds the status string to the status bar.

        Runs as an On After Check Callback.

        """
        if ((view is not None) and (selector is not None) and 
            isinstance(selector, StatusIdentifier) and selector.enable_status_string()):
            view.set_status(StatusIdentifier.StatusKey, selector.status_string)
    
    @staticmethod
    def erase_status_string(view = None, **kwargs):
        """Erases the status string from the status bar.

        Runs as an On Before Check Callback.

        """
        if view is not None:
            view.erase_status(StatusIdentifier.StatusKey)
    
    def enable_status_string(self):
        return True

StatusIdentifier.add_on_before_check_callback(StatusIdentifier.erase_status_string) 
StatusIdentifier.add_on_after_check_callback(StatusIdentifier.display_status_string)