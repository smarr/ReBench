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
import subprocess
import shutil
from threading import Lock
import time

from .model.data_point  import DataPoint
from .model.measurement import Measurement
from .model.run_id      import RunId


class DataStore(object):

    def __init__(self, ui):
        self._files = {}
        self._run_ids = {}
        self._bench_cfgs = {}
        self._ui = ui

    def load_data(self):
        for persistence in list(self._files.values()):
            persistence._load_data()

    def get(self, filename, discard_old_data):
        if filename not in self._files:
            self._files[filename] = _DataPointPersistence(filename, self,
                                                          discard_old_data,
                                                          self._ui)
        return self._files[filename]

    def create_run_id(self, benchmark, cores, input_size, var_value):
        if isinstance(cores, str) and cores.isdigit():
            cores = int(cores)
        if input_size == '':
            input_size = None
        if var_value == '':
            var_value = None

        run = RunId(benchmark, cores, input_size, var_value)
        if run in self._run_ids:
            return self._run_ids[run]
        else:
            self._run_ids[run] = run
            return run

    def get_config(self, name, vm_name, suite_name, extra_args):
        key = (name, vm_name, suite_name,
               '' if extra_args is None else str(extra_args))

        if key not in self._bench_cfgs:
            raise ValueError("Requested configuration is not available: " +
                             key.__str__())

        return self._bench_cfgs[key]

    def register_config(self, cfg):
        key = tuple(cfg.as_str_list())
        if key in self._bench_cfgs:
            raise ValueError("Two identical BenchmarkConfig tried to " +
                             "register. This seems to be wrong: " + str(key))
        else:
            self._bench_cfgs[key] = cfg
        return cfg

    @classmethod
    def get_by_file(cls, runs):
        by_file = {}
        for run in runs:
            points = run.get_data_points()
            run.discard_data_points()
            for point in points:
                measurements = point.get_measurements()
                for measure in measurements:
                    if measure.filename in by_file:
                        by_file[measure.filename].append(measure)
                    else:
                        by_file[measure.filename] = [measure]
        return by_file

    @classmethod
    def discard_data_of_runs(cls, runs, ui):
        by_file = cls.get_by_file(runs)
        for filename, measures in by_file.items():
            try:
                with open(filename, 'r') as data_file:
                    lines = data_file.readlines()
            except IOError:
                ui.debug_error_info(
                    "Tried to discard old data, but file does not seem to exist: %s\n" % filename)
                continue

            for measure in measures:
                lines[measure.line_number] = None

            lines = filter(None, lines)

            with open(filename, 'w') as data_file:
                data_file.writelines(lines)


class _DataPointPersistence(object):

    def __init__(self, data_filename, data_store, discard_old_data, ui):
        self._data_store = data_store
        self._ui = ui
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
            with open(self._data_filename, 'r') as data_file:
                self._process_lines(data_file)
        except IOError:
            self._ui.debug_error_info("No data loaded, since %s does not exist.\n"
                                      % self._data_filename)

    def _process_lines(self, data_file):
        """
         The most important assumptions we make here is that the total
         measurement is always the last one serialized for a data point.
        """
        errors = set()
        data_point = None

        previous_run_id = None
        line_number = 0
        for line in data_file:
            if line.startswith('#'):  # skip comments, and shebang lines
                line_number += 1
                continue

            try:
                measurement = Measurement.from_str_list(
                    self._data_store, line.rstrip('\n').split(self._SEP),
                    line_number, self._data_filename)

                run_id = measurement.run_id
                if previous_run_id is not run_id:
                    data_point = DataPoint(run_id)
                    previous_run_id = run_id

                data_point.add_measurement(measurement)

                if measurement.is_total():
                    run_id.loaded_data_point(data_point)
                    data_point = DataPoint(run_id)

            except ValueError as err:
                msg = str(err)
                if not errors:
                    self._ui.debug_error_info("Failed loading data from data file: "
                                              + data_file + "\n")
                if msg not in errors:
                    # Configuration is not available, skip data point
                    self._ui.debug_error_info("{ind}" + msg + "\n")
                    errors.add(msg)
            line_number += 1

    def _insert_shebang_line(self):
        """
        Insert a shebang (#!/path/to/executable) into the data file.
        This allows it theoretically to be executable.
        """
        shebang_line = "#!%s\n" % (subprocess.list2cmdline(sys.argv))

        try:
            # if file doesn't exist, just create it
            if not os.path.exists(self._data_filename):
                with open(self._data_filename, 'w') as data_file:
                    data_file.write(shebang_line)
                    data_file.flush()
                    data_file.close()
                return

            # if file exists, the first line might already be the same line
            with open(self._data_filename, 'r') as data_file:
                if data_file.readline() == shebang_line:
                    return

            # otherwise, copy the file and insert line at the beginning
            renamed_file = "%s-%.0f.tmp" % (self._data_filename, time.time())
            os.rename(self._data_filename, renamed_file)
            with open(self._data_filename, 'w') as data_file:
                data_file.write(shebang_line)
                data_file.flush()
                shutil.copyfileobj(open(renamed_file, 'r'), data_file)
            os.remove(renamed_file)
        except Exception as err:  # pylint: disable=broad-except
            self._ui.error(
                "Error: While inserting a shebang line into the data file.\n{ind}%s\n" % err)

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
