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
    def __init__(self, host, port, root, schema, logger, aggreg_time=1):
        """ Create a new graphite service.

        @param host: Graphite server name or IP
        @param port: Graphite server plaintext protocol port 
        @param root: Path to append to all metric paths sent
        @param schema: Schema defining how to aggregate metrics. This is a dictionary
                       and should include an entry for every path metric that may be
                       added (without the root) set to either 'sum' or 'avg'
        @param logger: Logger object. Only used for debugging - errors are raised.
        @param aggred_time: Time over which to aggregate. This must be at least 1 second,
                            otherwise the values sent to Graphite will be wrong.
        @raises: FailedToConnect
        """
        self.host = host
        self.port = port
        self.root = root
        self.schema = schema
        self.logger = logger
        self.aggreg_time = aggreg_time
        self.values = {} 
        self.socket = None
        self._connect()
    
    def _connect(self):
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
            self.socket.connect((self.host, self.port))
        except (socket.error, socket.herror, socket.gaierror, socket.timeout) as e:
            raise FailedToConnect()

    def add(self, name, value):
        """ Add a new metric path and value

        @param path: Metric path. Must be declared in schema;
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
     
    def flush(self):
        """ Send any values added more than aggreg_time ago to the Graphite
            server
        """
        time_now = int(time.time())
        messages = []
        clear = []
        # Find messages to send
        for add_time in self.values:
            if add_time + self.aggreg_time > time_now:
                break
            clear.append(add_time)
            for name in self.values[add_time]:
                if self.schema[name] == 'sum':
                    value = sum(self.values[add_time][name])
                elif self.schema[name] == 'avg':
                    value = sum(self.values[add_time][name]) / float(len(self.values[add_time][name]))                        
                else:
                    raise UnknownSchema()
                message = "{root}.{name} {value} {timestamp}\n".format(
                    root=self.root,
                    name=name,
                    value=value,
                    timestamp=add_time
                )
                messages.append(message)
        # Clear up
        for add_time in clear:
            del self.values[add_time]
        # And send
        if len(messages) > 0:
            message = ''.join(messages)
            self.logger.debug(message)
            self._send(message)

    def _send(self, data, recon=True):
        """ Send the data to the graphite server
       
        @param data: String to send to the server
        @param retry: If true, will attempt to re-connect to the server and retry on error
        """
        try:
            self.socket.sendall(data)
        except (socket.error, socket.timeout) as e:
            if retry:
                self._connect()
                self._send(data, False)
            else:
                raise FailedToConnect()

    def close(self):
        """Close the connection to the server"""
        self.socket.close()
