import re

class InfoError(Exception):
    """ Exception raised when failing to update info"""
    pass

class BoxInfo(object):
    """ BoxInfo

        This class is used to gather information about the system this is running on.
        Objects of this class have three properties that can be read:

        - mem: Dictionary as {
            'total': (total memory in bytes), 
            'used': (used memory in bytes), 
            'free': (free memory in bytes)
        }
        - swap: Dictionary as {
            'total': (total swap space in bytes),
            'used': (used swap space in bytes),
            'free': (free swp space in bytes)
        }
        - cpu: Dictionary as {
            'loadavg': {
                '1min': 1 minute load average,
                '5min': 5 minute load average,
                '15min': 15 minute load average
            }
        - io: Dictionary as {
            (device name): {
                'read': {
                    'bytes': (Total number of bytes read on the device),
                    'ms': (Total number of milliseconds spent reading on the device)
                },
                'write': {
                    'bytes': (Total number of bytes written to the device),
                    'ms': (Total number of milliseconds spent writting on the device)
                }
            }
     
        Call refresh on the object to refresh those statistics.
   """
    def __init__(self, devices=None):
        """ Create a new BoxInfo object and read initial statistics """
        self._devices = []
        if devices:
            for d in devices:
                if ':' in d:
                    entry = tuple(d.split(':')[0:2])
                else:
                    entry = (d, d)
                self._devices.append(entry)
        self.unit_fact = {'b': 1, 'kb': 1024, 'mb': 1024*1024, 'gb': 1024*1024*1024}
        self.meminfo_pattern = re.compile(r'^(?P<label>\S+):\s+(?P<value>\S+)\s+(?P<unit>\S+)$')
        self.loadavg_pattern = re.compile(r'^(?P<avg1min>[0-9.]+) (?P<avg5min>[0-9.]+) (?P<avg15min>[0-9.]+) (\d+)/(\d+) (\d+)$')
        # See https://www.kernel.org/doc/Documentation/block/stat.txt
        self.block_stat_pattern = re.compile(r'^\s*' + r'\s+'.join([
            r'(?P<readios>\d+)',
            r'(?P<readmerges>\d+)',
            r'(?P<readsectors>\d+)',
            r'(?P<readticks>\d+)',
            r'(?P<writeios>\d+)',
            r'(?P<writemerges>\d+)',
            r'(?P<writesectors>\d+)',
            r'(?P<writeticks>\d+)',
            r'(?P<infligh>\d+)',
            r'(?P<ioticks>\d+)',
            r'(?P<timeinqueue>\d+)'
        ]) + '\s*$')
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
                    'loadavg': {
                        '1min': float(m['avg1min']), 
                        '5min': float(m['avg5min']), 
                        '15min': float(m['avg15min'])
                    }
                } 
        # Get IO stat values for selected devices
        try:
            for device in self._devices:
                with open('/sys/block/' + device[0] + '/stat') as f:
                    line = f.readline()
                    p = self.block_stat_pattern.match(line)
                    if p:
                        m = p.groupdict()
                        self.io[device[1]] = {
                            'read': {
                                 'bytes': int(m['readsectors']) * 512,
                                 'ms': int(m['readticks'])
                            },
                            'write': {
                                'bytes': int(m['writesectors']) * 512,
                                'ms': int(m['writeticks'])
                            }
                        }
        except IOError:
            raise InfoError()
        if len(self.mem) == 0 or len(self.swap) == 0 or len(self.cpu) == 0 or len(self.io) != len(self._devices):
            raise InfoError()
