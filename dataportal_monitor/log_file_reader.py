class LogFileNotFound(Exception):
    """Exception raised when the log file is not found"""
    pass

class LogFileReader(object):
    # FIXME: Need to detect log rotations!
    # FIXME: Detect file not found
    def __init__(self, file_name):
        self.file_name = file_name
        self.file = None
        self._open()

    def _open(self):
        if self.file:
            self.file.close()
        self.file = open(self.file_name, 'r')
        self.file.seek(0, 2)

    def close(self):
        self.file.close()
        self.file = None

    def readline(self):
        line = self.file.readline() 
        return line

