# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from __future__ import with_statement, print_function
from collections import deque

from datetime import datetime
from httplib import HTTPException
from time import time
import logging
import json
import urllib2
import urllib
import re

from .statistics import StatisticProperties


class Reporter(object):

    def __init__(self):
        self._job_completion_reported = False

    def run_failed(self, run_id, cmdline, return_code, output):
        pass
    
    def run_completed(self, run_id, statistics, cmdline):
        pass
    
    def job_completed(self, run_ids):
        if not self._job_completion_reported:
            self.report_job_completed(run_ids)
            self._job_completion_reported = True
    
    def set_total_number_of_runs(self, num_runs):
        pass
    
    def start_run(self, run_id):
        pass
    

class TextReporter(Reporter):
    
    def __init__(self):
        super(TextReporter, self).__init__()

    def _configuration_details(self, run_id, statistics = None):
        result = ["\t".join(run_id.as_str_list()), " = "]
        self._output_stats(result, run_id, statistics)
        return result
    
    def _output_stats(self, output_list, run_id, statistics):
        if not statistics:
            return
        
        for field, value in statistics.__dict__.iteritems():
            if not field.startswith('_'):
                output_list.append("%s: %s " % (field, value))

    @staticmethod
    def _path_to_string(path):
        out = [path[0].as_simple_string()]
        for item in path[1:]:
            if item:
                out.append(str(item))
        return " ".join(out) + " "
    
    def _generate_all_output(self, run_ids):
        rows = []
        col_width = None

        for run_id in run_ids:
            stats = StatisticProperties(run_id.get_total_values(),
                                        run_id.requested_confidence_level)
            out = run_id.as_str_list()
            self._output_stats(out, run_id, stats)
            if col_width is None:
                col_width = [0] * len(out)
            rows.append(out)
            col_width = [max(len(col_content), col)
                         for col_content, col in zip(out, col_width)]

        for row in rows:
            result = "  ".join([col.ljust(width)
                                for col, width in zip(row, col_width)])
            yield result


class CliReporter(TextReporter):
    """ Reports to standard out using the logging framework """
    
    def __init__(self, _cfg):
        super(CliReporter, self).__init__()
        self._num_runs       = None
        self._runs_completed = 0
        self._startTime      = None
        self._runs_remaining = 0
        
        # TODO: re-add support, think, we need that based on the proper config, i.e., the run id
#         self._min_runtime = configurator.statistics.min_runtime

    def run_failed(self, run_id, cmdline, return_code, output):
        # Additional information in debug mode
        result = "[%s] Run failed: %s\n" % (
            datetime.now(),
            " ".join(self._configuration_details(run_id)))
        logging.debug(result)
        
        # Standard error output
        if return_code == -9:
            log_msg = "Run timed out. return_code: %s"
        else:
            log_msg = "Run failed return_code: %s"
        
        print(log_msg % return_code)
        
        print("Cmd: %s\n" % cmdline)
        
        if run_id.bench_cfg.suite.has_max_runtime():
            logging.debug("max_runtime: %s" % run_id.bench_cfg.suite.max_runtime)
        logging.debug("cwd: %s" % run_id.bench_cfg.suite.location)
        
        if output and len(output.strip()) > 0:
            print("Output:\n%s\n" % output)    

    def run_completed(self, run_id, statistics, cmdline):
        result = "[%s] Run completed: %s\n" % (
            datetime.now(),
            " ".join(self._configuration_details(run_id, statistics)))
        
        logging.debug(result)
        
        self._runs_completed += 1
        self._runs_remaining -= 1

        if run_id.run_config.min_runtime:
            if statistics.mean < run_id.run_config.min_runtime:
                print(("WARNING: measured mean is lower than min_runtime (%s) "
                      "\t mean: %.1f [%.1f, %.1f]\trun id: %s")
                      % (run_id.run_config.min_runtime,
                         statistics.mean, statistics.conf_interval_low,
                         statistics.conf_interval_high,
                         run_id.as_simple_string()))
                print("Cmd: %s" % cmdline)

    def report_job_completed(self, run_ids):
        print("[%s] Job completed" % datetime.now())
        for line in self._generate_all_output(run_ids):
            print(line)
    
    def set_total_number_of_runs(self, num_runs):
        self._num_runs = num_runs
        self._runs_remaining = num_runs
    
    def start_run(self, run_id):
        if self._runs_completed > 0:
            current = time()
            
            etl = ((current - self._startTime) / self._runs_completed *
                   self._runs_remaining)
            sec = etl % 60
            m   = (etl - sec) / 60 % 60
            h   = (etl - sec - m) / 60 / 60
            print(("Run %s \t runs left: %00d \t " +
                   "time left: %02d:%02d:%02d") % (run_id.bench_cfg.name,
                                                   self._runs_remaining,
                                                   round(h), round(m),
                                                   round(sec)))
        else:
            self._startTime = time()
            print("Run %s \t runs left: %d" % (run_id.bench_cfg.name,
                                               self._runs_remaining))
            
    def _output_stats(self, output_list, run_id, statistics):
        if not statistics:
            return
        
        if run_id.run_failed():
            output_list.append("run failed.")
            output_list.append("")
            output_list.append("")
            output_list.append("")
        else:
            output_list.append("mean:")
            output_list.append(("%.1f" % statistics.mean).rjust(8))
            output_list.append("[" +
                               ("%.1f" % statistics.conf_interval_low).rjust(8)
                               + ",")
            output_list.append(("%.1f" % statistics.conf_interval_high).rjust(8)
                               + "]")


class FileReporter(TextReporter):
    """ should be mainly a log file
        data is the responsibility of the data_aggregator
    """
    
    def __init__(self, filename):
        super(FileReporter, self).__init__()
        self._file = open(filename, 'a+')

    def run_failed(self, run_id, cmdline, return_code, output):
        result = "[%s] Run failed: %s\n" % (
            datetime.now(),
            " ".join(self._configuration_details(run_id)))
        self._file.writelines(result)
        
    def run_completed(self, run_id, statistics, cmdline):
        result = "[%s] Run completed: %s\n" % (
            datetime.now(),
            " ".join(self._configuration_details(run_id, statistics)))
        self._file.writelines(result)
    
    def report_job_completed(self, run_ids):
        self._file.write("[%s] Job completed\n" % datetime.now())
        for line in self._generate_all_output(run_ids):
            self._file.write(line + "\n")
            
        self._file.close()


class IrcReporter(TextReporter):
    """ Reports to IRC """

    try:
        from irc.bot import SingleServerIRCBot
        from threading import Thread

        IRC_SUPPORT = True

        class _Bot(SingleServerIRCBot):
            def __init__(self, cfg):
                IrcReporter.SingleServerIRCBot.__init__(self,
                                                        [(cfg.server, cfg.port)],
                                                        cfg.nick, cfg.nick)
                self._cfg = cfg
                self._terminate = False
                self._msg_queue = deque()
                self._last_send = time()
                self._pause_between_msgs = 1.0  # second

            def on_nicknameinuse(self, c, e):
                c.nick(c.get_nickname() + "_")

            def on_welcome(self, c, e):
                c.join(self._cfg.channel)

            def send(self, msg):
                self._msg_queue.appendleft(msg)

            def terminate(self):
                self._terminate = True

            def _send_msg(self):
                if self._msg_queue:
                    if time() - self._last_send >= self._pause_between_msgs:
                        msg = self._msg_queue.pop()
                        self.connection.privmsg(self._cfg.channel, msg)
                        self._last_send = time()

            def start(self, timeout = 0.2):
                self._connect()
                while not self._terminate:
                    self.manifold.process_once(timeout)
                    self._send_msg()
                self.disconnect()

    except ImportError:
        IRC_SUPPORT = False

    def __init__(self, cfg):
        super(IrcReporter, self).__init__()
        if not IrcReporter.IRC_SUPPORT:
            logging.error("IRC support not available. "
                          "Please install irc>=8.9.1 from PyPI, "
                          "or remove IRC reporting in configuration")
            import sys
            sys.exit(1)
        self._cfg = cfg
        self._client = IrcReporter._Bot(cfg)

        def thread_main():
            self._client.start()

        t = IrcReporter.Thread(target=thread_main)
        t.start()

    def _format_msg(self, msg):
        if self._cfg.notify:
            return "%s: %s" % (self._cfg.notify, msg)
        else:
            return msg

    def run_failed(self, run_id, cmdline, return_code, output):
        if not self._cfg.report_run_failed:
            return

        # Standard error output
        if return_code == -9:
            return_detail = "timed out. return_code: %s" % return_code
        else:
            return_detail = "exited normally. return_code: %s" % return_code

        # Additional information in debug mode
        msg = "Run failed: %s; %s" % (
            " ".join(self._configuration_details(run_id)),
            return_detail)
        msg = self._format_msg(msg)
        self._client.send(msg)

    def run_completed(self, run_id, statistics, cmdline):
        if not self._cfg.report_run_completed:
            return

        msg = "Run completed: %s" % (
            " ".join(self._configuration_details(run_id, statistics)))
        msg = self._format_msg(msg)
        self._client.send(msg)

    def report_job_completed(self, run_ids):
        if not self._cfg.report_job_completed:
            return
        self._client.send(self._format_msg("ReBench Job completed"))
        self._client.terminate()

# TODO: re-add support for CSV file generation for overview statistics
# class CSVFileReporter(Reporter):
#     """ Will generate a CSV file for processing in another program
#         as for instance R, Excel, or Numbers """
#
#     def __init__(self, cfg):
#         super(CSVFileReporter, self).__init__()
#         self._file = open(cfg.csv_file, 'a+')
#         self._cfg = cfg
#
#     def _prepareHeaderRow(self, data, data_aggregator, parameterMappings):
#         # since the data might be irregular find the item with the most
#         # parameters first
#         longestTuple = max(data.keys(), key=lambda tpl: len(tpl))
#         # and determine table width
#         table_width = len(longestTuple)
#
#         # now generate the header
#
#         # get sorted parameter mapping first
#         mapping = sorted(parameterMappings.items(), key=lambda entry:  entry[1])
#
#         header_row = []
#         for (title, _index) in mapping:
#             header_row.append(title)
#
#         # add empty columns to keep table aligned
#         while len(header_row) < table_width:
#             header_row.append('')
#
#         # now the statistic rows
#         for title in StatisticProperties.tuple_mapping():
#             header_row.append(title)
#
#         return header_row, table_width
#
#     def report_job_completed(self, run_ids):
#         old_locale = locale.getlocale(locale.LC_ALL)
#         if self._cfg.csv_locale:
#             locale.setlocale(locale.LC_ALL, self._cfg.csv_locale)
#
#
#         # get the data to be processed
#         data = data_aggregator.getDataFlattend()
#         parameterMappings = data_aggregator.data_mapping()
#         num_common_parameters = len(parameterMappings)
#
#         header_row, max_num_parameters = self._prepareHeaderRow(data, data_aggregator, parameterMappings)
#
#         table = []
#
#         # add the header row
#         table.append(header_row)
#
#         # add the actual results to the table
#         for run, measures in data.iteritems():
#             row = []
#             row += run[0:num_common_parameters]            # add the common ones
#             row += [''] * (max_num_parameters - len(run))  # add fill for unused parameters
#             row += run[num_common_parameters:]             # add all remaining
#             row += list(StatisticProperties(measures,
#                                             self._cfg.confidence_level).as_tuple()) # now add the actual result data
#             table.append(row)
#
#         for row in table:
#             self._file.write(";".join([i if type(i) == str else locale.format("%f", i or 0.0) for i in row]) + "\n")
#
#         self._file.close()
#         locale.setlocale(locale.LC_ALL, old_locale)
    

class CodespeedReporter(Reporter):
    """
    This report will report the recorded data on the completion of the job
    to the configured Codespeed instance.
    """
    
    def __init__(self, cfg):
        super(CodespeedReporter, self).__init__()
        self._cfg = cfg
        self._incremental_report = self._cfg.report_incrementally
        self._cache_for_seconds = 30
        self._cache = {}
        self._last_send = time()

    def run_completed(self, run_id, statistics, cmdline):
        if not self._incremental_report:
            return
        
        # ok, talk to codespeed immediately
        self._cache[run_id] = self._format_for_codespeed(run_id, statistics)

        if time() - self._last_send >= self._cache_for_seconds:
            self._send_and_empty_cache()

    def _send_and_empty_cache(self):
        self._send_to_codespeed(self._cache.values())
        self._cache = {}
    
    def _result_data_template(self):
        # all None values have to be filled in
        return {
            'commitid':     self._cfg.commit_id,
            'project':      self._cfg.project,
            #'revision_date': '', # Optional. Default is taken either
                                  # from VCS integration or from current date
            'executable':   None,
            'benchmark':    None,
            'environment':  self._cfg.environment,
            'branch':       self._cfg.branch,
            'result_value': None,
            # 'result_date': datetime.today(), # Optional
            'std_dev':      None,
            'max':          None,
            'min':          None}

    @staticmethod
    def _beautify_benchmark_name(name):
        """
        Currently just remove all bench, or benchmark strings.
        """
        replace = re.compile('bench(mark)?', re.IGNORECASE)
        return replace.sub('', name)

    def _format_for_codespeed(self, run_id, stats = None):
        result = self._result_data_template()
        
        if stats and not run_id.run_failed():
            result['min']          = stats.min
            result['max']          = stats.max
            result['std_dev']      = stats.std_dev
            result['result_value'] = stats.mean
        else:
            result['result_value'] = -1
        
        result['executable'] = self._cfg.executable or run_id.bench_cfg.vm.name

        if run_id.bench_cfg.codespeed_name:
            name = run_id.bench_cfg.codespeed_name
        else:
            name = (self._beautify_benchmark_name(run_id.bench_cfg.name)
                    + " (%(cores)s cores, %(input_sizes)s %(extra_args)s)")

        # TODO: this is incomplete:
        name = name % {'cores'       : run_id.cores_as_str,
                       'input_sizes' : run_id.input_size_as_str,
                       'extra_args'  : run_id.bench_cfg.extra_args}
        
        result['benchmark'] = name
        
        return result

    def _send_payload(self, payload):
        fh = urllib2.urlopen(self._cfg.url, payload)
        response = fh.read()
        fh.close()
        logging.info("Results were sent to codespeed, response was: "
                     + response)

    def _send_to_codespeed(self, results):
        payload = urllib.urlencode({'json': json.dumps(results)})

        try:
            self._send_payload(payload)
        except (IOError, HTTPException):
            # sometimes codespeed fails to accept a request because something
            # is not yet properly initialized, let's try again for those cases
            try:
                self._send_payload(payload)
            except (IOError, HTTPException) as error:
                logging.error(str(error) + " This is most likely caused by "
                              "either a wrong URL in the config file, or an "
                              "environment not configured in codespeed. URL: "
                              + self._cfg.url)

        logging.info("Sent %d results to codespeed." % len(results))

    def _prepare_result(self, run_id):
        stats = StatisticProperties(run_id.get_total_values(),
                                    run_id.requested_confidence_level)
        return self._format_for_codespeed(run_id, stats)

    def report_job_completed(self, run_ids):
        if self._incremental_report:
            # send remaining items from cache
            self._send_and_empty_cache()
            return

        results = [self._prepare_result(run_id) for run_id in run_ids]

        # now, send them of to codespeed
        self._send_to_codespeed(results)
