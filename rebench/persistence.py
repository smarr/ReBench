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
import json
import os
import shutil
import subprocess
import sys
from tempfile import NamedTemporaryFile
from threading import Lock
from time import time

from .environment import determine_environment, determine_source_details
from .model.data_point  import DataPoint
from .model.measurement import Measurement
from .model.profile_data import ProfileData
from .model.run_id      import RunId
from .rebenchdb         import get_current_time
from .ui                import UIError

_START_TIME_LINE = "# Execution Start: "


class DataStore(object):

    def __init__(self, ui):
        self._files = {}
        self._run_ids = {}
        self._bench_cfgs = {}
        self.ui = ui

    def load_data(self, runs, discard_run_data):
        for persistence in list(self._files.values()):
            persistence.load_data(runs, discard_run_data)

    def get(self, filename, configurator, action):
        if filename not in self._files:
            source = determine_source_details(configurator)
            if configurator.use_rebench_db and source['commitId'] is None:
                raise UIError("Reporting to ReBenchDB is enabled, "
                              + "but failed to obtain source details. "
                              + "If ReBench is run outside of the relevant repo "
                              + "set the path with --git-repo", None)
            if configurator.use_rebench_db and 'repo_url' in configurator.rebench_db:
                source['repoURL'] = configurator.rebench_db['repo_url']

            if configurator.options and configurator.options.branch:
                source['branchOrTag'] = configurator.options.branch

            if action == "profile":
                p = _ProfileFilePersistence(filename, self, configurator, self.ui)
            else:
                p = _FilePersistence(filename, self, configurator, self.ui)
            self.ui.debug_output_info('ReBenchDB enabled: {e}\n', e=configurator.use_rebench_db)

            if configurator.use_rebench_db:
                if action == "profile":
                    db = _ProfileReBenchDB(configurator, self, self.ui)
                else:
                    db = _ReBenchDB(configurator, self, self.ui)
                p = _CompositePersistence(p, db)

            self._files[filename] = p
        return self._files[filename]

    def create_run_id(self, benchmark, cores, input_size, var_value, machine):
        if isinstance(cores, str) and cores.isdigit():
            cores = int(cores)
        if input_size == '':
            input_size = None
        if var_value == '':
            var_value = None

        run = RunId(benchmark, cores, input_size, var_value, machine)
        if run in self._run_ids:
            return self._run_ids[run]
        else:
            self._run_ids[run] = run
            return run

    def get_config(self, name, executor_name, suite_name, extra_args):
        key = (name, executor_name, suite_name,
               '' if extra_args is None else str(extra_args))

        if key not in self._bench_cfgs:
            raise ValueError("Requested configuration is not available: " +
                             str(key))

        return self._bench_cfgs[key]

    def register_config(self, cfg):
        key = tuple(cfg.as_str_list())
        if key in self._bench_cfgs:
            raise ValueError("Two identical BenchmarkConfig tried to " +
                             "register. This seems to be wrong: " + str(key))
        self._bench_cfgs[key] = cfg
        return cfg


class _AbstractPersistence(object):

    def load_data(self, runs, discard_run_data):
        """
        Needs to be implemented by subclass.
        It is expected to return the start time of the recording.
        The _CompositePersistence is using it then for _ReBenchDBPresistence.
        """

    def loaded_data_point(self, data_point):
        """Needs to be implemented by subclass"""

    def persist_data_point(self, data_point):
        """Needs to be implemented by subclass"""

    def run_completed(self):
        """Needs to be implemented by subclass"""

    def close(self):
        """Needs to be implemented by subclass"""


class _ConcretePersistence(_AbstractPersistence):

    def __init__(self, data_store, ui):
        self._data_store = data_store
        self._start_time = None
        self.ui = ui


class _CompositePersistence(_AbstractPersistence):

    def __init__(self, file_pers, rebench_db):
        self._file = file_pers
        self._rebench_db = rebench_db
        self._closed = False

    def load_data(self, runs, discard_run_data):
        start_time = self._file.load_data(runs, discard_run_data)
        # TODO: if load data into ReBenchDB
        self._rebench_db.set_start_time(start_time)
        self._rebench_db.send_data()
        return start_time

    def loaded_data_point(self, data_point):
        # TODO: if load data into ReBenchDB
        self._rebench_db.persist_data_point(data_point)

    def persist_data_point(self, data_point):
        self._file.persist_data_point(data_point)
        self._rebench_db.persist_data_point(data_point)

    def run_completed(self):
        self._rebench_db.send_data()

    def close(self):
        if not self._closed:
            self._file.close()
            self._rebench_db.close()
            self._closed = True


class _FilePersistence(_ConcretePersistence):

    def __init__(self, data_filename, data_store, configurator, ui):
        super(_FilePersistence, self).__init__(data_store, ui)
        if not data_filename:
            raise ValueError("DataPointPersistence expects a filename " +
                             "for data_filename, but got: %s" % data_filename)

        self._data_filename = data_filename
        self._file = None
        if configurator.discard_old_data:
            self._discard_old_data()
        self._lock = Lock()
        self._read_start_time()
        if not self._start_time:
            self._start_time = get_current_time()

        self._configurator = configurator

    def _discard_old_data(self):
        self._truncate_file(self._data_filename)

    @staticmethod
    def _truncate_file(filename):
        # pylint: disable-next=unspecified-encoding
        with open(filename, 'w'):
            pass

    def _read_start_time(self):
        if not os.path.exists(self._data_filename):
            self._start_time = None
            return
        # pylint: disable-next=unspecified-encoding
        with open(self._data_filename, 'r') as data_file:
            self._start_time = self._read_first_meta_block(data_file)

    @staticmethod
    def _read_first_meta_block(data_file):
        for line in data_file:
            if not line.startswith('#'):
                # really only read the first set of commented lines, i.e. the first meta block
                return None
            if line.startswith(_START_TIME_LINE):
                return line[len(_START_TIME_LINE):].strip()
        return None

    def load_data(self, runs, discard_run_data):
        """
        Loads the data from the configured data file
        """
        if discard_run_data:
            current_runs = {run for run in runs if run.is_persisted_by(self)}
        else:
            current_runs = None

        try:
            if current_runs:
                with NamedTemporaryFile('w', delete=False) as target:
                    # pylint: disable-next=unspecified-encoding
                    with open(self._data_filename, 'r') as data_file:
                        self._process_lines(data_file, current_runs, target)
                    os.unlink(self._data_filename)
                    shutil.move(target.name, self._data_filename)
            else:
                # pylint: disable-next=unspecified-encoding
                with open(self._data_filename, 'r') as data_file:
                    self._process_lines(data_file, current_runs, None)
        except IOError:
            self.ui.debug_error_info("No data loaded, since %s does not exist.\n"
                                      % self._data_filename)
        return self._start_time

    def _process_lines(self, data_file, runs, filtered_data_file):
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
                if filtered_data_file:
                    filtered_data_file.write(line)
                continue

            try:
                data_point, previous_run_id = self._parse_data_line(
                    data_point, line, line_number, runs, filtered_data_file, previous_run_id)
            except ValueError as err:
                msg = str(err)
                if not errors:
                    self.ui.debug_error_info("Failed loading data from data file: "
                                              + self._data_filename + "\n")
                if msg not in errors:
                    # Configuration is not available, skip data point
                    self.ui.debug_error_info("{ind}" + msg + "\n")
                    errors.add(msg)

    def _parse_data_line(
            self, data_point, line, line_number, runs, filtered_data_file, previous_run_id):
        measurement = Measurement.from_str_list(
            self._data_store, line.rstrip('\n').split(self._SEP),
            line_number, self._data_filename)

        run_id = measurement.run_id
        if filtered_data_file and runs and run_id in runs:
            return data_point, previous_run_id

        # these are all the measurements that are not filtered out
        if filtered_data_file:
            filtered_data_file.write(line)

        if previous_run_id is not run_id:
            data_point = DataPoint(run_id)
            previous_run_id = run_id

        data_point.add_measurement(measurement)

        if measurement.is_total():
            run_id.loaded_data_point(data_point,
                                     (measurement.iteration <= run_id.warmup_iterations
                                      if run_id.warmup_iterations else False))
            data_point = DataPoint(run_id)
        return data_point, previous_run_id

    _SEP = "\t"  # separator between serialized parts of a measurement

    def _open_file_and_append_execution_comment(self):
        """
        Append a shebang (#!/path/to/executable) to the data file.
        This allows it theoretically to be executable.
        But more importantly also records execution metadata to reproduce the data.
        """
        shebang_with_metadata = "#!%s\n" % (subprocess.list2cmdline(sys.argv))
        shebang_with_metadata += _START_TIME_LINE + self._start_time + "\n"
        shebang_with_metadata += "# Environment: " + json.dumps(determine_environment()) + "\n"
        shebang_with_metadata += "# Source: " + json.dumps(
            determine_source_details(self._configurator)) + "\n"

        csv_header = self._SEP.join(Measurement.get_column_headers()) + "\n"

        try:
            # pylint: disable-next=unspecified-encoding,consider-using-with
            data_file = open(self._data_filename, 'a+')
            is_empty = data_file.tell() == 0
            data_file.write(shebang_with_metadata)
            if is_empty:
                data_file.write(csv_header)
            data_file.flush()
            return data_file
        except Exception as err:  # pylint: disable=broad-except
            raise UIError(
                "Error: Was not able to open data file for writing.\n{ind}%s\n%s\n" % (
                    os.getcwd(), err),
                err)


    def _persists_data_point_in_open_file(self, data_point):
        for measurement in data_point.get_measurements():
            line = self._SEP.join(measurement.as_str_list())
            self._file.write(line + "\n")

    def persist_data_point(self, data_point):
        """
        Serialize all measurements of the data point and persist them
        in the data file.
        """
        with self._lock:
            self._open_file_to_add_new_data()
            self._persists_data_point_in_open_file(data_point)
            self._file.flush()

    def run_completed(self):
        """Nothing to be done."""

    def _open_file_to_add_new_data(self):
        if not self._file:
            self._file = self._open_file_and_append_execution_comment()

    def close(self):
        if self._file:
            self._file.close()
            self._file = None


class _ProfileFilePersistence(_FilePersistence):
    def _persists_data_point_in_open_file(self, data_point):
        assert isinstance(data_point, ProfileData)
        line = self._SEP.join(data_point.as_str_list())
        assert "\n" not in line, "The newline character is now allowed in a data line"
        self._file.write(line + "\n")

    def _parse_data_line(
            self, data_point, line, line_number, runs, filtered_data_file, previous_run_id):
        str_list = line.rstrip('\n').split(self._SEP)

        data_point = ProfileData.from_str_list(
            self._data_store, str_list, line_number, self._data_filename)

        run_id = data_point.run_id
        if filtered_data_file and runs and run_id in runs:
            return data_point

        # these are all the measurements that are not filtered out
        if filtered_data_file:
            filtered_data_file.write(line)

        run_id.loaded_data_point(data_point, False)
        return data_point, run_id


class _ReBenchDB(_ConcretePersistence):

    def __init__(self, configurator, data_store, ui):
        super(_ReBenchDB, self).__init__(data_store, ui)
        # TODO: extract common code, possibly
        self._configurator = configurator
        self._rebench_db = configurator.get_rebench_db_connector()

        self._lock = Lock()

        self._cache_for_seconds = 30
        self._cache = {}
        self._last_send = time()

    def set_start_time(self, start_time):
        assert self._start_time is None
        self._start_time = start_time

    def load_data(self, runs, discard_run_data):
        raise RuntimeError("Does not yet support data loading from ReBenchDB")

    def persist_data_point(self, data_point):
        with self._lock:
            if data_point.run_id not in self._cache:
                self._cache[data_point.run_id] = []
            self._cache[data_point.run_id].append(data_point)

    def send_data(self):
        current_time = time()
        time_past = current_time - self._last_send
        self.ui.debug_output_info(
            "ReBenchDB: data last send {seconds}s ago\n",
            seconds=round(time_past, 2))
        if time_past >= self._cache_for_seconds:
            self._send_data_and_empty_cache()
            self._last_send = time()

    def _send_data_and_empty_cache(self):
        if self._cache:
            if self._send_data(self._cache):
                self._cache = {}

    def convert_data_to_api_format(self, data):
        num_measurements = 0
        all_data = []
        criteria = {}
        for run_id, data_points in data.items():
            dp_data = []
            for dp in data_points:
                measurements = dp.measurements_as_dict(criteria)
                num_measurements += len(measurements['m'])
                dp_data.append(measurements)
            all_data.append({
                'runId': run_id.as_dict(),
                'd': dp_data
            })

        criteria_index = []
        for c, idx in criteria.items():
            criteria_index.append({'c': c[0], 'u': c[1], 'i': idx})

        return all_data, criteria_index, num_measurements

    def convert_data_to_api_20_format(self, data):
        num_measurements = 0
        all_data = []
        criteria = {}
        for run_id, data_points in data.items():
            dp_data = []
            for dp in data_points:
                num_measurements += dp.add_measurements_api_v20(criteria, dp_data)
            all_data.append({
                'runId': run_id.as_dict(),
                'd': dp_data
            })

        criteria_index = []
        for c, idx in criteria.items():
            criteria_index.append({'c': c[0], 'u': c[1], 'i': idx})

        return all_data, criteria_index, num_measurements

    def _send_data(self, cache):
        self.ui.debug_output_info("ReBenchDB: Prepare data for sending\n")
        if self._rebench_db.is_api_v2():
            all_data, criteria_index, num_measurements = self.convert_data_to_api_20_format(cache)
        else:
            all_data, criteria_index, num_measurements = self.convert_data_to_api_format(cache)

        self.ui.debug_output_info(
            "ReBenchDB: Sending {num_m} measures. startTime: {st}\n",
            num_m=num_measurements, st=self._start_time)
        return self._rebench_db.send_results({
            'data': all_data,
            'criteria': criteria_index,
            'env': determine_environment(),
            'startTime': self._start_time,
            'source': determine_source_details(self._configurator)}, num_measurements)

    def close(self):
        with self._lock:
            self._send_data_and_empty_cache()


class _ProfileReBenchDB(_ReBenchDB):

    def _send_data(self, cache):
        self.ui.debug_output_info("ReBenchDB: Prepare data for sending\n")
        num_profiles = 0
        all_data = []
        for run_id, data_points in cache.items():
            profile_data = [dp.as_dict() for dp in data_points]
            num_profiles += len(profile_data)
            all_data.append({
                'runId': run_id.as_dict(),
                'p': profile_data
            })

        self.ui.debug_output_info(
            "ReBenchDB: Sending {num_m} profiles. startTime: {st}\n",
            num_m=num_profiles, st=self._start_time)
        return self._rebench_db.send_results({
            'data': all_data,
            'env': determine_environment(),
            'startTime': self._start_time,
            'source': determine_source_details(self._configurator)}, num_profiles)
