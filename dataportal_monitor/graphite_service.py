import re
import fnmatch
import types
import socket
import time

class FailedToConnect(Exception):
    """ Exception raised when failing to connect/reconnect to the Graphite server"""
    pass

class UnknownSchema(Exception):
    """ Exception raised when an unkwon schema type is used"""
    pass 
    
class GraphiteService(object):
    """ GraphiteService
 
        Class used to send values to a graphite server
    """
    def __init__(self, host, port, root, schema, logger, aggreg_time=1, timeout=60):
        """ Create a new graphite service.

        @param host: Graphite server name or IP
        @param port: Graphite server plaintext protocol port 
        @param root: Path to append to all metric paths sent
        @param schema: Schema defining how to aggregate metrics. This is a dictionary
                       and should include an entry for every path metric that may be
                       added (without the root, unix-style shell wildcards are accepted).
                       The supported values are 'sum', 'avg', 'min', 'max' or a user defined
                       function;
        @param logger: Logger object. Only used for debugging - errors are raised.
        @param aggred_time: Time over which to aggregate. This must be at least 1 second,
                            otherwise the values sent to Graphite will be wrong.
        @param timeout: Connection timeout
        @raises: FailedToConnect
        """
        self.host = host
        self.port = port
        self.root = root
        self.logger = logger
        self.aggreg_time = aggreg_time
        self.timeout = timeout
        self.values = {} 
        self.messages = []
        self.socket = None
        self.schema = schema
        self._schema_re = [] 
        for expr in self.schema:
            self._schema_re.append({
                'regexp': re.compile(fnmatch.translate(expr)),
                'aggregate': self.schema[expr]
            })
    
    def connect(self):
        """ Attempt to connect to the graphite server

        @raises: FailedToConnect
        """
        if self.socket:
            try:
                self.socket.close()
            except socket.error:
                pass
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
        except (socket.error, socket.herror, socket.gaierror, socket.timeout) as e:
            self.socket = None
            raise FailedToConnect()

    def add(self, name, value):
        """ Add a new metric path and value

        @param path: Metric path. If this does not match any entry in the schema, then 'avg' will be used 
        @param value: Value for the path. Must be a number
        """
        time_now = int(time.time())
        if time_now in self.values:
            if name in self.values[time_now]:
                self.values[time_now][name].append(value)
            else:
                self.values[time_now][name] = [value]
        else:
            self.values[time_now] = {name: [value]}
    
    def _aggregate(self, name, values):
        """ Aggregate the list of values according to schema
 
        @param name: Metric path to aggregrate
        @param values: List of values to aggregate
        @raise: UnknownSchema
        @return: Aggregated value
        """
        # Find the aggregator to use
        agg = 'avg'
        if name in self.schema:
            agg = self.schema[name]
        else:
            for match in self._schema_re:
                if match['regexp'].match(name):
                    agg = match['aggregate'] 
                    break
        # Apply the aggregation
        if type(agg) == types.FunctionType:
            return agg(values) 
        elif agg == 'sum':
            return sum(values)
        elif agg == 'avg':
            return sum(values) / float(len(values))
        elif agg == 'max':
            return max(values)
        elif agg == 'min':
            return min(values)

    def flush(self):
        """ Send any values added more than aggreg_time ago to the Graphite
            server. Will automatically connect to the server if not connected.

        @raise: FailedToConnect
        """
        time_now = int(time.time())
        clear = []
        # Find messages to send
        for add_time in self.values:
            if add_time + self.aggreg_time > time_now:
                break
            clear.append(add_time)
            for name in self.values[add_time]:
                value = self._aggregate(name, self.values[add_time][name])
                message = "{root}.{name} {value} {timestamp}\n".format(
                    root=self.root,
                    name=name,
                    value=value,
                    timestamp=add_time
                )
                self.messages.append(message)
        # Clear up
        for add_time in clear:
            del self.values[add_time]
        # And send
        if len(self.messages) > 0:
            message = ''.join(self.messages)
            self.logger.debug(message)
            try:
                self._send(message)
            except FailedToConnect:
                raise
            else:
                self.messages = [] 

    def _send(self, data, retry=True):
        """ Send the data to the graphite server
        
        Will automatically connect to the server if not connected.
 
        @param data: String to send to the server
        @param retry: If true, will attempt to re-connect to the server and retry on error
        @raise: FailedToconnect
        """
        if not self.socket:
            self.connect()
        try:
            self.socket.sendall(data)
        except (socket.error, socket.timeout) as e:
            if retry:
                self.connect()
                self._send(data, False)
            else:
                raise FailedToConnect()

    def close(self):
        """Close the connection to the server"""
        if self.socket:
            self.socket.close()
            self.socket = None
