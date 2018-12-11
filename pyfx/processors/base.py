

class Processor:
    """
    Base class for all processors.
    """

    def __init__(self):

        r = "".join([random.choice(string.ascii_letters) for i in range(10)])
        self._id = "{}_{}".format(type(self).__name__,r)

    def _get_properties():
        """
        Return a dictionary of properties used by workspace.
        """
        
        return {}

    @property
    def id(self):

        return self._id

    @property
    def properties(self):

        return self._get_properties()
