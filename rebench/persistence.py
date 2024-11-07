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
from collections.abc import Mapping
from tempfile import NamedTemporaryFile
from threading import Lock
from time import time
from typing import TYPE_CHECKING

from .environment import determine_environment, determine_source_details
from .model.benchmark import Benchmark
from .model.data_point  import DataPoint
from .model.measurement import Measurement
from .model.profile_data import ProfileData
from .model.run_id      import RunId
from .output            import UIError
from .rebenchdb         import get_current_time

if TYPE_CHECKING:
    from .ui import UI

_START_TIME_LINE = "# Execution Start: "


class DataStore(object):

    def __init__(self, ui: "UI"):
        self._files: dict[str, "AbstractPersistence"] = {}
        self._run_ids: dict[RunId, RunId] = {}
        self._benchmarks: dict[Benchmark, Benchmark] = {}
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
                source["branchOrTag"] = configurator.options.branch

            if action == "profile":
                p = _ProfileFilePersistence(filename, self, configurator, self.ui)
            else:
                p = _FilePersistence(filename, self, configurator, self.ui)
            self.ui.debug_output_info("ReBenchDB enabled: {e}\n", e=configurator.use_rebench_db)

            if configurator.use_rebench_db:
                if action == "profile":
                    db = _ProfileReBenchDB(configurator, self, self.ui)
                else:
                    db = _ReBenchDB(configurator, self, self.ui)
                p = _CompositePersistence(p, db)

            self._files[filename] = p
        return self._files[filename]

    def create_run_id(self, benchmark: Benchmark, cores, input_size, var_value, tag, machine):
        if isinstance(cores, str) and cores.isdigit():
            cores = int(cores)
        if input_size == "":
            input_size = None
        if var_value == "":
            var_value = None
        if machine == "":
            machine = None

        run = RunId(benchmark, cores, input_size, var_value, tag, machine)
        return self._ensure_run_id_objects_are_unique(run)

    def create_benchmark_from_dict(self, d):
        bench = Benchmark.from_dict(d)
        return self._ensure_benchmarks_are_unique(bench)

    def create_run_id_from_dict(self, d: Mapping, benchmark: Benchmark):
        run = RunId.from_dict(d, benchmark)
        return self._ensure_run_id_objects_are_unique(run)

    def _ensure_run_id_objects_are_unique(self, run_id: RunId):
        if run_id in self._run_ids:
            return self._run_ids[run_id]

        self._run_ids[run_id] = run_id
        return run_id

    def _ensure_benchmarks_are_unique(self, benchmark: Benchmark):
        if benchmark in self._benchmarks:
            return self._benchmarks[benchmark]

        self._benchmarks[benchmark] = benchmark
        return benchmark


class AbstractPersistence(object):

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


class _ConcretePersistence(AbstractPersistence):

    def __init__(self, data_store: DataStore, ui):
        self._data_store = data_store
        self._start_time = None
        self.ui = ui


class _CompositePersistence(AbstractPersistence):

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


def _to_json(data):
    return json.dumps(data, separators=(",", ":"), ensure_ascii=True)

_METADATA_RUN_ID = "# run_id: "
_METADATA_BENCHMARK = "# benchmark: "

class _FilePersistence(_ConcretePersistence):

    def __init__(self, data_filename, data_store: DataStore, configurator, ui):
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

        self._run_ids_in_file: dict[RunId, int] = {}
        self._id_to_run_id: list[RunId] = []

        self._benchmarks_in_file: dict[Benchmark, int] = {}
        self._id_to_benchmark: list[Benchmark] = []

    def _discard_old_data(self):
        self._truncate_file(self._data_filename)

    @staticmethod
    def _truncate_file(filename):
        # pylint: disable-next=unspecified-encoding
        with open(filename, "w"):
            pass

    def _read_start_time(self):
        if not os.path.exists(self._data_filename):
            self._start_time = None
            return
        # pylint: disable-next=unspecified-encoding
        with open(self._data_filename, "r") as data_file:
            self._start_time = self._read_first_meta_block(data_file)

    @staticmethod
    def _read_first_meta_block(data_file):
        for line in data_file:
            if not line.startswith("#"):
                # really only read the first set of commented lines, i.e. the first meta block
                return None
            if line.startswith(_START_TIME_LINE):
                return line[len(_START_TIME_LINE) :].strip()
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
                with NamedTemporaryFile("w", delete=False) as target:
                    # pylint: disable-next=unspecified-encoding
                    with open(self._data_filename, "r") as data_file:
                        self._process_lines(data_file, current_runs, target)
                    os.unlink(self._data_filename)
                    shutil.move(target.name, self._data_filename)
            else:
                # pylint: disable-next=unspecified-encoding
                with open(self._data_filename, "r") as data_file:
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
        csv_header = self._get_csv_header()

        previous_run_id = None
        line_number = 0
        for line in data_file:
            if line.startswith("#"):  # skip comments, and shebang lines, but read run_ids
                line_number += 1
                if filtered_data_file:
                    filtered_data_file.write(line)

                if line.startswith(_METADATA_BENCHMARK):
                    rest_line = line[len(_METADATA_BENCHMARK):]
                    bench_id, bench_json = rest_line.split("=", 1)
                    bench_dict = json.loads(bench_json)
                    benchmark = self._data_store.create_benchmark_from_dict(bench_dict)
                    assert benchmark not in self._benchmarks_in_file
                    self._benchmarks_in_file[benchmark] = int(bench_id)
                    assert len(self._id_to_benchmark) == int(bench_id)
                    self._id_to_benchmark.append(benchmark)

                elif line.startswith(_METADATA_RUN_ID):
                    rest_line = line[len(_METADATA_RUN_ID):]
                    run_id_id, run_json = rest_line.split("=", 1)
                    run_dict = json.loads(run_json)
                    assert "benchmark_id" in run_dict
                    benchmark_id = int(run_dict["benchmark_id"])
                    benchmark = self._id_to_benchmark[benchmark_id]

                    run_id = self._data_store.create_run_id_from_dict(run_dict, benchmark)
                    self._run_ids_in_file[run_id] = int(run_id_id)
                    assert len(self._id_to_run_id) == int(run_id_id)
                    self._id_to_run_id.append(run_id)
                continue

            if line == csv_header:
                continue

            try:
                data_point, previous_run_id = self._parse_data_line(
                    data_point, line, line_number, runs, filtered_data_file, previous_run_id)
            except (ValueError, IndexError) as err:
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
            self._id_to_run_id, line.rstrip('\n').split(self._SEP),
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

    def _get_csv_header(self):
        return self._SEP.join(Measurement.get_column_headers()) + "\n"

    def _open_file_and_append_execution_comment(self):
        """
        Append a shebang (#!/path/to/executable) to the data file.
        This allows it theoretically to be executable.
        But more importantly also records execution metadata to reproduce the data.
        """
        shebang_with_metadata = "#!%s\n" % (subprocess.list2cmdline(sys.argv))
        shebang_with_metadata += _START_TIME_LINE + self._start_time + "\n"
        shebang_with_metadata += "# Environment: " + _to_json(determine_environment()) + "\n"
        shebang_with_metadata += "# Source: " + _to_json(
            determine_source_details(self._configurator)) + "\n"

        csv_header = self._get_csv_header()

        try:
            # pylint: disable-next=unspecified-encoding,consider-using-with
            data_file = open(self._data_filename, "a+")
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

    def _ensure_benchark_is_persisted(self, benchmark: Benchmark) -> int:
        if benchmark not in self._benchmarks_in_file:
            bench_id = len(self._benchmarks_in_file)
            line = _METADATA_BENCHMARK + str(bench_id) + "=" + _to_json(benchmark.as_dict()) + "\n"
            self._file.write(line) # type: ignore
            self._benchmarks_in_file[benchmark] = bench_id
        return self._benchmarks_in_file[benchmark]

    def _ensure_run_id_is_persisted(self, run_id: RunId) -> int:
        if run_id not in self._run_ids_in_file:
            run_id_id = len(self._run_ids_in_file)
            benchmark_id = self._ensure_benchark_is_persisted(run_id.benchmark)

            run = run_id.as_dict(True)
            run["benchmark_id"] = benchmark_id
            assert "benchmark" not in run

            line = _METADATA_RUN_ID + str(run_id_id) + "=" + _to_json(run) + "\n"
            self._file.write(line) # type: ignore
            self._run_ids_in_file[run_id] = run_id_id
        return self._run_ids_in_file[run_id]

    def _persists_data_point_in_open_file(self, data_point: DataPoint):
        run_id_id = self._ensure_run_id_is_persisted(data_point.run_id)
        for measurement in data_point.get_measurements():
            line = self._SEP.join(measurement.as_str_list(run_id_id))
            self._file.write(line + "\n") # type: ignore

    def persist_data_point(self, data_point: DataPoint):
        """
        Serialize all measurements of the data point and persist them
        in the data file.
        """
        with self._lock:
            self._open_file_to_add_new_data()
            self._persists_data_point_in_open_file(data_point)
            self._file.flush() # type: ignore

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
        run_id_id = self._ensure_run_id_is_persisted(data_point.run_id)
        assert isinstance(data_point, ProfileData)
        line = self._SEP.join(data_point.as_str_list(run_id_id))
        assert "\n" not in line, "The newline character is now allowed in a data line"
        self._file.write(line + "\n")

    def _parse_data_line(
            self, data_point, line, line_number, runs, filtered_data_file, previous_run_id):
        str_list = line.rstrip('\n').split(self._SEP)

        data_point = ProfileData.from_str_list(
            self._id_to_run_id, str_list, line_number, self._data_filename)

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
                num_measurements += len(measurements["m"])
                dp_data.append(measurements)
            all_data.append({
                'runId': run_id.as_dict(),
                'd': dp_data
            })

        criteria_index = []
        for c, idx in criteria.items():
            criteria_index.append({"c": c[0], "u": c[1], "i": idx})

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
            criteria_index.append({"c": c[0], "u": c[1], "i": idx})

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
