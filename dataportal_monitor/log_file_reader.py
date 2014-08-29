import os

class LogFileAbsent(Exception):
    """Exception raised when the log file is not found, or has been removed and not replaced"""
    pass

class LogFileReader(object):
    """ Read lines from log files, handling log rotations

        The log roation will be detected if the file is renamed (and a new file with the actual
        name is then created), or if the file is truncated to a size smaller than the current
        size.
    """
    def __init__(self, file_name):
        """ Create a new log file reader

        @param file_name: The file name
        """
        self.file_name = file_name
        self.file = None

    def reset(self, tail=True):
        """ Re-open the log file, and seek to the last entry 
        @param tail: If true, seek to the end of the file. Otherwise start at the begining.
        @raises: LogFileAbsent
        """
        if self.file:
            self.file.close()
        try:
            self.file = open(self.file_name, 'r')
        except IOError:
            self.file = None
            raise LogFileAbsent()
        if tail:
            self.file.seek(0, 2)
        else:
           self.file.seek(0)

    def close(self):
        """ Close the reader """
        if self.file:
            self.file.close()
            self.file = None

    def readline(self):
        """ Get the next line from the log file.
 
        This will attempt to open the log file if it is
        not open.

        @raises: LogFileAbsent
        @return: The next line, or an empty string if there is no new line.
        """
        if not self.file:
            self.reset()
        line = self.file.readline() 
        if not line:
            try:
                tstat = os.stat(self.file_name)
            except OSError:
                # It looks like the file has been renamed/deleted, but no new file took it's place.
                # Wait for that to happen. TODO: Should this raise instead?
                pass
            pos = self.file.tell()
            fstat = os.fstat(self.file.fileno())
            # Check if file had been renamed or truncated. This only works so well: if data the same size of larger
            # than the existing size is added to the file after truncation, we won't detect it.
            if (fstat.st_ino != tstat.st_ino) or (self.file.tell() > tstat.st_size):
                self.reset(tail=False)
                line = self.file.readline()
        return line

