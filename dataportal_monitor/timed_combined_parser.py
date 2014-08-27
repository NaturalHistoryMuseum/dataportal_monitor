import re

class ParseError(Exception):
    """ Raised on parsing errors """
    pass

class TimedCombinedParser(object):
    """ TimedCombinedParser
       
        This class is used to parse individual lines from an nginx log file. The log format **must** be set
        to:

        log_format timed_combined '$remote_addr - $remote_user [$time_iso8601] '
                                  '"$request" $status $body_bytes_sent '
                                  '"$http_referer" "$http_user_agent" '
                                  '$request_time $upstream_response_time';
    """
    def __init__(self):
        """" Create a new parser """
        # Prepare regexp for parsing
        parts = [
            r'(?P<host>\S+)',
            r'\S+',
            r'(?P<user>\S+)',
            r'\[(?P<time>.+)\]',
            r'"(?P<request>.*)"',
            r'(?P<status>[0-9]+)',
            r'(?P<bytes_sent>\S+)',
            r'"(?P<referrer>.*)"',
            r'"(?P<agent>.*)"',
            r'(?P<request_time>\S+)',
            r'(?P<upstream_time>\S+)'
        ]
        self.pattern = re.compile(r'\s+'.join(parts)+r'\s*\Z')
 
    def parse(self, line):
        """ Parse the given line, and return a dictionary defining:

              host, user, time (not parsed), request, status, bytes_sent, referrer, agent, request_time,  upstream_time

             bytes_sent, request_time and upstream_time and cast to float (and '-' is replaced with 0.0). Other values
             (and in particular time) are left un-parsed.

             @param line: line from nging/apache log file
             @return: Dict if the status code is 2xx or 3xx, None othwerwise
             @raises: ParseError when the line cannot be parsed
        """
        # Parse the line
        m = self.pattern.match(line)
        if not m:
            raise ParseError()

        info = m.groupdict()

        # Skip errors
        status = int(info['status'])
        if status < 200 or status >= 400:
            return None
   
        # Replace '-' by 0 in numberic fields, and cast to float.
        for field in ['bytes_sent', 'request_time', 'upstream_time']:
            if info[field] == '-':
                info[field] = 0.0
            else:
                info[field] = float(info[field])
        
        # Parse time
        # info['time'] = int((dateutil.parser.parse(info['time']) - datetime(1970, 1, 1,tzinfo=tzutc())).total_seconds())
        return info

