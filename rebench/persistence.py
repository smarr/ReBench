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
from datetime import datetime
from tempfile import NamedTemporaryFile
from threading import Lock
from time import time

from .configuration_error import ConfigurationError
from .environment import determine_environment, determine_source_details
from .model.data_point  import DataPoint
from .model.measurement import Measurement
from .model.run_id      import RunId


try:
    from http.client import HTTPException
    from urllib.request import urlopen, Request as PutRequest
except ImportError:
    # Python 2.7
    from httplib import HTTPException
    from urllib2 import urlopen, Request


    class PutRequest(Request):
        def __init__(self, *args, **kwargs):
            if 'method' in kwargs:
                del kwargs['method']
            Request.__init__(self, *args, **kwargs)

        def get_method(self, *_args, **_kwargs):  # pylint: disable=arguments-differ
            return 'PUT'


_START_TIME_LINE = "# Execution Start: "


class DataStore(object):

    def __init__(self, ui):
        self._files = {}
        self._run_ids = {}
        self._bench_cfgs = {}
        self._ui = ui

    def load_data(self, runs, discard_run_data):
        for persistence in list(self._files.values()):
            persistence.load_data(runs, discard_run_data)

    def get(self, filename, configurator):
        if filename not in self._files:
            if configurator.use_rebench_db and 'repo_url' in configurator.rebench_db:
                _source['repoURL'] = configurator.rebench_db['repo_url']

            if configurator.options and configurator.options.branch:
                _source['branchOrTag'] = configurator.options.branch

            p = _FilePersistence(filename, self, configurator.discard_old_data, self._ui)
            self._ui.debug_output_info('ReBenchDB enabled: {e}\n', e=configurator.use_rebench_db)

            if configurator.use_rebench_db:
                if 'project_name' not in configurator.rebench_db:
                    raise ConfigurationError(
                        "No project_name defined in configuration file under reporting.rebenchdb.")

                if not configurator.options.experiment_name:
                    raise ConfigurationError(
                        "The experiment was not named, which is mandatory. "
                        "This is needed to identify the data uniquely. "
                        "It should also help to remember in which context it "
                        "was recorded, perhaps relating to a specific CI job "
                        "or confirming some hypothesis."
                        "\n\n"
                        "Use the --experiment option to set the name.")

                db = _ReBenchDB(configurator.rebench_db['db_url'],
                                configurator.rebench_db['project_name'],
                                configurator.options.experiment_name,
                                self, self._ui)
                p = _CompositePersistence(p, db)

            self._files[filename] = p
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

    def get_config(self, name, executor_name, suite_name, extra_args):
        key = (name, executor_name, suite_name,
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
        self._bench_cfgs[key] = cfg
        return cfg


_environment = determine_environment()
_source = determine_source_details()


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
        self._ui = ui


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

    def __init__(self, data_filename, data_store, discard_old_data, ui):
        super(_FilePersistence, self).__init__(data_store, ui)
        if not data_filename:
            raise ValueError("DataPointPersistence expects a filename " +
                             "for data_filename, but got: %s" % data_filename)

        self._data_filename = data_filename
        self._file = None
        if discard_old_data:
            self._discard_old_data()
        self._append_execution_comment()
        self._lock = Lock()

    def _discard_old_data(self):
        self._truncate_file(self._data_filename)

    @staticmethod
    def _truncate_file(filename):
        with open(filename, 'w'):
            pass

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
                    with open(self._data_filename, 'r') as data_file:
                        self._process_lines(data_file, current_runs, target)
                    os.unlink(self._data_filename)
                    shutil.move(target.name, self._data_filename)
            else:
                with open(self._data_filename, 'r') as data_file:
                    self._process_lines(data_file, current_runs, None)
        except IOError:
            self._ui.debug_error_info("No data loaded, since %s does not exist.\n"
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
                if line.startswith(_START_TIME_LINE):
                    start_time = line[len(_START_TIME_LINE):].strip()
                    if self._start_time is None or self._start_time > start_time:
                        self._start_time = start_time

                line_number += 1
                if filtered_data_file:
                    filtered_data_file.write(line)
                continue

            try:
                measurement = Measurement.from_str_list(
                    self._data_store, line.rstrip('\n').split(self._SEP),
                    line_number, self._data_filename)

                run_id = measurement.run_id
                if filtered_data_file and runs and run_id in runs:
                    continue

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

            except ValueError as err:
                msg = str(err)
                if not errors:
                    self._ui.debug_error_info("Failed loading data from data file: "
                                              + self._data_filename + "\n")
                if msg not in errors:
                    # Configuration is not available, skip data point
                    self._ui.debug_error_info("{ind}" + msg + "\n")
                    errors.add(msg)

    def _append_execution_comment(self):
        """
        Append a shebang (#!/path/to/executable) to the data file.
        This allows it theoretically to be executable.
        But more importantly also records execution metadata to reproduce the data.
        """
        shebang_line = "#!%s\n" % (subprocess.list2cmdline(sys.argv))
        if not self._start_time:
            self._start_time = datetime.utcnow().isoformat() + "+00:00"
            shebang_line += _START_TIME_LINE + self._start_time + "\n"
        shebang_line += "# Environment: " + json.dumps(_environment) + "\n"
        shebang_line += "# Source: " + json.dumps(_source) + "\n"

        try:
            # if file doesn't exist, just create it
            if not os.path.exists(self._data_filename):
                with open(self._data_filename, 'w') as data_file:
                    data_file.write(shebang_line)
                    data_file.flush()
                    data_file.close()
                return

            # otherwise, append the lines
            with open(self._data_filename, 'a') as data_file:
                data_file.write(shebang_line)
                data_file.flush()
        except Exception as err:  # pylint: disable=broad-except
            self._ui.error(
                "Error: While appending metadata to the data file.\n{ind}%s\n" % err)

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

    def run_completed(self):
        """Nothing to be done."""

    def _open_file_to_add_new_data(self):
        if not self._file:
            self._file = open(self._data_filename, 'a+')

    def close(self):
        if self._file:
            self._file.close()
            self._file = None


class _ReBenchDB(_ConcretePersistence):

    def __init__(self, server_url, project_name, experiment_name, data_store, ui):
        super(_ReBenchDB, self).__init__(data_store, ui)
        # TODO: extract common code, possibly
        if not server_url:
            raise ValueError("ReBenchDB expected server address, but got: %s" % server_url)

        self._ui.debug_output_info(
            'ReBench will report all measurements to {url}\n', url=server_url)
        self._server_url = server_url
        self._project_name = project_name
        self._experiment_name = experiment_name
        self._lock = Lock()

        self._cache_for_seconds = 30
        self._cache = {}
        self._last_send = time()

    def set_start_time(self, start_time):
        assert self._start_time is None
        self._start_time = start_time

    def load_data(self, runs, discard_run_data):
        raise Exception("Does not yet support data loading from ReBenchDB")

    def persist_data_point(self, data_point):
        with self._lock:
            if data_point.run_id not in self._cache:
                self._cache[data_point.run_id] = []
            self._cache[data_point.run_id].append(data_point)

    def send_data(self):
        current_time = time()
        time_past = current_time - self._last_send
        self._ui.debug_output_info(
            "ReBenchDB: data last send {seconds}s ago\n",
            seconds=round(time_past, 2))
        if time_past >= self._cache_for_seconds:
            self._send_data_and_empty_cache()
            self._last_send = time()

    def _send_data_and_empty_cache(self):
        if self._cache:
            if self._send_data(self._cache):
                self._cache = {}

    def _send_data(self, cache):
        self._ui.debug_output_info("ReBenchDB: Prepare data for sending\n")
        num_measurements = 0
        all_data = []
        criteria = {}
        for run_id, data_points in cache.items():
            dp_data = []
            for dp in data_points:
                measurements = dp.measurements_as_dict(criteria)
                num_measurements += len(measurements['m'])
                dp_data.append(measurements)
            data = dict()
            data['runId'] = run_id.as_dict()
            data['d'] = dp_data
            all_data.append(data)

        criteria_index = []
        for c, idx in criteria.items():
            criteria_index.append({'c': c[0], 'u': c[1], 'i': idx})

        self._ui.debug_output_info(
            "ReBenchDB: Send {num_m} measures. startTime: {st}\n",
            num_m=num_measurements, st=self._start_time)
        return self._send_to_rebench_db({
            'data': all_data,
            'criteria': criteria_index,
            'env': _environment,
            'startTime': self._start_time,
            'projectName': self._project_name,
            'experimentName': self._experiment_name,
            'source': _source}, num_measurements)

    def close(self):
        with self._lock:
            self._send_data_and_empty_cache()

    def _send_payload(self, payload):
        req = PutRequest(self._server_url, payload,
                         {'Content-Type': 'application/json'}, method='PUT')
        socket = urlopen(req)
        response = socket.read()
        socket.close()
        return response

    def _send_to_rebench_db(self, results, num_measurements):
        payload = json.dumps(results, separators=(',', ':'), ensure_ascii=True)

        # self._ui.output("Saving JSON Payload of size: %d\n" % len(payload))
        with open("payload.json", "w") as text_file:
            text_file.write(payload)

        try:
            data = payload.encode('utf-8')
            response = self._send_payload(data)
            self._ui.verbose_output_info(
                "ReBenchDB: Sent {num_m} results to ReBenchDB, response was: {resp}\n",
                num_m=num_measurements, resp=response)
            return True
        except TypeError as te:
            self._ui.error("{ind}Error: Reporting to ReBenchDB failed.\n"
                           + "{ind}{ind}" + str(te) + "\n")
        except (IOError, HTTPException):
            # sometimes Codespeed fails to accept a request because something
            # is not yet properly initialized, let's try again for those cases
            try:
                response = self._send_payload(payload)
                self._ui.verbose_output_info(
                    "ReBenchDB: Sent {num_m} results to ReBenchDB, response was: {resp}\n",
                    num_m=num_measurements, resp=response)
                return True
            except (IOError, HTTPException) as error:
                self._ui.error("{ind}Error: Reporting to ReBenchDB failed.\n"
                               + "{ind}{ind}" + str(error) + "\n")
        return False
