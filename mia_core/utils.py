import urllib.parse


class UrlBuilder:
    """The URL builder.

    Attributes:
        base_path (str): the base path
        params (list[Param]): The query parameters
    """
    base_path = None
    params = []

    def __init__(self, start_url):
        """Constructs a new URL builder.

        Args:
            start_url (str): The URL to start with
        """
        pos = start_url.find("?")
        if pos == -1:
            self.base_path = start_url
            return
        self.base_path = start_url[:pos]
        self.params = []
        for piece in start_url[pos+1:].split("&"):
            pos = piece.find("=")
            name = urllib.parse.unquote(piece[:pos])
            value = urllib.parse.unquote(piece[pos+1:])
            self.params.append(self.Param(name, value))

    def add_param(self, name, value):
        """Adds a query parameter.

        Args:
            name (str): The parameter name
            value (str): The parameter value

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        self.params.append(self.Param(name, value))
        return self

    def del_param(self, name):
        """Removes a query parameter.

        Args:
            name (str): The parameter name

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        self.params = [x for x in self.params if x.name != name]
        return self

    def set_param(self, name, value):
        """Sets a query parameter.  The current parameters with the
        same name will be replaced.

        Args:
            name (str): The parameter name
            value (str): The parameter value

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        return self.del_param(name).add_param(name, value)

    def __str__(self):
        return self.base_path + "&".join([str(x) for x in self.params])

    class Param:
        """A query parameter.

        Attributes:
            name (str): The parameter name
            value (str): The parameter value
        """
        name = None
        value = None

        def __init__(self, name, value):
            """Constructs a new query parameter

            Args:
                name (str): The parameter name
                value (str): The parameter value
            """
            self.name = name
            self.value = value

        def __str__(self):
            """Returns the string representation of this query
            parameter.

            Returns:
                str: The string representation of this query
                    parameter
            """
            return "%s=%s" % (
                urllib.parse.quote(self.name),
                urllib.parse.quote(self.value))
