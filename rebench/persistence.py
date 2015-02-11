# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import os
import sys
import logging
import subprocess
import shutil
from threading import Lock
import time

from .model.data_point  import DataPoint
from .model.measurement import Measurement


class DataPointPersistence(object):
    _registry = {}

    @classmethod
    def reset(cls):
        cls._registry = {}

    @classmethod
    def load_data(cls):
        for persistence in cls._registry.values():
            persistence._load_data()

    @classmethod
    def get(cls, filename, discard_old_data):
        if filename not in cls._registry:
            cls._registry[filename] = DataPointPersistence(filename,
                                                           discard_old_data)
        return cls._registry[filename]

    def __init__(self, data_filename, discard_old_data):
        if not data_filename:
            raise ValueError("DataPointPersistence expects a filename " +
                             "for data_filename, but got: %s" % data_filename)
        
        self._data_filename = data_filename
        self._file = None
        if discard_old_data:
            self._discard_old_data()
        self._insert_shebang_line()
        self._lock = Lock()
    
    def _discard_old_data(self):
        self._truncate_file(self._data_filename)

    @staticmethod
    def _truncate_file(filename):
        with open(filename, 'w'):
            pass
    
    def _load_data(self):
        """
        Loads the data from the configured data file
        """
        try:
            with open(self._data_filename, 'r') as f:
                self._process_lines(f)
        except IOError:
            logging.info("No data loaded %s does not exist."
                         % self._data_filename)
    
    def _process_lines(self, f):
        """
         The most important assumptions we make here is that the total
         measurement is always the last one serialized for a data point.
        """
        errors = set()
        
        previous_run_id = None
        for line in f:
            if line.startswith('#'):  # skip comments, and shebang lines
                continue
            
            try:
                measurement = Measurement.from_str_list(line.rstrip('\n').
                                                        split(self._SEP))
                run_id = measurement.run_id
                if previous_run_id is not run_id:
                    data_point      = DataPoint(run_id)
                    previous_run_id = run_id
                
                data_point.add_measurement(measurement)
                
                if measurement.is_total():
                    run_id.loaded_data_point(data_point)
                    data_point = DataPoint(run_id)
            
            except ValueError, e:
                msg = str(e)
                if msg not in errors:
                    # Configuration is not available, skip data point
                    logging.log(logging.DEBUG - 1, msg)
                    errors.add(msg)
    
    def _insert_shebang_line(self):
        """
        Insert a shebang (#!/path/to/executable) into the data file.
        This allows it theoretically to be executable.
        """
        shebang_line = "#!%s\n" % (subprocess.list2cmdline(sys.argv))
        
        try:
            # if file doesn't exist, just create it
            if not os.path.exists(self._data_filename):
                with open(self._data_filename, 'w') as f:
                    f.write(shebang_line)
                    f.flush()
                    f.close()
                return

            # if file exists, the first line might already be the same line
            with open(self._data_filename, 'r') as f:
                if f.readline() == shebang_line:
                    return

            # otherwise, copy the file and insert line at the beginning
            renamed_file = "%s-%.0f.tmp" % (self._data_filename, time.time()) 
            os.rename(self._data_filename, renamed_file)
            with open(self._data_filename, 'w') as f:
                f.write(shebang_line)
                f.flush()
                shutil.copyfileobj(open(renamed_file, 'r'), f)
            os.remove(renamed_file)
        except Exception as e:
            logging.error("An error occurred " +
                          "while trying to insert a shebang line: %s", e)

    _SEP = "\t"  # separator between serialized parts of a measurement

    def persist_data_point(self, data_point):
        """
        Serialize all measurements of the data point and persist them
        in the data file.
        """
        with self._lock:
            self._open_file_to_add_new_data()

            for measurement in data_point.get_measurements():
                line = self._SEP.join(measurement.as_str_list())
                self._file.write(line + "\n")

            self._file.flush()

    def _open_file_to_add_new_data(self):
        if not self._file:
            self._file = open(self._data_filename, 'a+')
