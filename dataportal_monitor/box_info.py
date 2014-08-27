import re

class InfoError(Exception):
    """ Exception raised when failing to update info"""
    pass

class BoxInfo(object):
    """ BoxInfo

        This class is used to gather information about the system this is running on.
        Objects of this class have three properties that can be read:

        - mem: Dictionary, defining 'total', 'used', 'free';
        - swap: Dictionary, defining 'total', 'used', free';
        - cpu, Dictionary, defining 'loadavg1min', 'loadavg5min' and 'loadavg15min';
        - io defining a dictionary with nothing.
     
        Call refresh on the object to refresh those statistics.
   """
    def __init__(self):
        """ Create a new BoxInfo object and read initial statistics """
        self.unit_fact = {'b': 1, 'kb': 1024, 'mb': 1024*1024, 'gb': 1024*1024*1024}
        self.meminfo_pattern = re.compile(r'^(?P<label>\S+):\s+(?P<value>\S+)\s+(?P<unit>\S+)$')
        self.loadavg_pattern = re.compile(r'^(?P<avg1min>[0-9.]+) (?P<avg5min>[0-9.]+) (?P<avg15min>[0-9.]+) (\d+)/(\d+) (\d+)$')
        self.refresh()

    def refresh(self):
        """ Refresh the statistics """
        self.mem = {}
        self.swap = {}
        self.cpu = {}
        self.io = {}
        # Get memory values
        with open('/proc/meminfo') as f:
            line = f.readline()
            while line:
                p = self.meminfo_pattern.match(line)
                if p:
                    m = p.groupdict() 
                    label = m['label']
                    value = int(m['value']) * self.unit_fact[m['unit'].lower()]
                    if label == 'MemTotal':
                        self.mem['total'] = value
                    elif label == 'MemFree':
                        self.mem['free'] = value
                    elif label == 'SwapTotal':
                        self.swap['total'] = value
                    elif label == 'SwapFree':
                        self.swap['free'] = value
                line = f.readline()
        self.mem['used'] = self.mem['total'] - self.mem['free']
        self.swap['used'] = self.swap['total'] - self.swap['free']
        # Get CPU values
        with open('/proc/loadavg') as f:
            line = f.readline()
            p = self.loadavg_pattern.match(line)
            if p:
                m = p.groupdict()
                self.cpu = {
                    'loadavg1min': float(m['avg1min']), 
                    'loadavg5min': float(m['avg5min']), 
                    'loadavg15min': float(m['avg15min'])
                } 
        if len(self.mem) == 0 or len(self.swap) == 0 or len(self.cpu) == 0:
            raise InfoError()

