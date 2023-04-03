import json


class InsitePlugin:

    parameters = {}

    """
       Initialization function
       parameters - dictonary of named attributes
    """

    def init(self, parameters):
        self.parameters = parameters

    """
       Returns true if we can pass more then 1 host in through the hosts field in the fetch function
    """

    def can_group(self):
        return False

    """
       Fetches the details for the provided host
       Will return a json formatted string of the form
       @param hosts The list of hosts(ip||name) that we will fetch metrics for
       {
          "fields" : {
             "fieldname": "value",
             "fieldname": value,
             ...
          },
          "host" : "host",
          "name" : "plugin-name"
       }
       May also return an array of these objects [{...}, {...}, ...]
    """

    def fetch(self, hosts):
        return None

    """
       Fetches the details for the provided host
       Will return a json formatted string of the form
       @param hosts, A list of hosts that we want to poll.  This will always
                     contain a single host unless can_group() returns true in
                     which all hosts we want to poll will be pushed into the
                     hosts array in a single call
       @return a single document of the structure
       {
          "fields" : {
             "fieldname": "value",
             "fieldname": value,
             ...
          },
          "host" : "host",
          "name" : "plugin-name"
       }
       or
       an array of these objects [{...}, {...}, ...]
    """

    def do_fetch(self, hosts):
        return self.fetch([] + hosts)

    """
       Cleanup any lingering resources/sockets/connections
    """

    def dispose(self):
        pass
