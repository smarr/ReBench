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
from ..configuration_error import ConfigurationError
import rebench.reporter as reporter


class Reporting(object):
    
    def __init__(self, raw_config, options):
        self._csv_file   = raw_config.get('csv_file',   None)
        self._csv_locale = raw_config.get('csv_locale', None)
        self._csv_raw    = raw_config.get('csv_raw',    None)
        
        self._confidence_level = raw_config.get('confidence_level', 0.95)

        if "codespeed" in raw_config and options.use_codespeed:
            self._codespeed = CodespeedReporting(raw_config, options)
        else:
            self._codespeed = None

        if "irc" in raw_config:
            self._irc = IrcReporting(raw_config, options)
        else:
            self._irc = None

        self._cli_reporter = reporter.CliReporter(self)

        # if self._config.reporting:
        #     if ('codespeed' in self._config.reporting and
        #         self._config.options.use_codespeed):
        #         reporters.append(CodespeedReporter(self._config))
    
    @property
    def csv_file(self):
        return self._csv_file
    
    @property
    def csv_locale(self):
        return self._csv_locale
    
    @property
    def csv_raw(self):
        return self._csv_raw
    
    @property
    def confidence_level(self):
        return self._confidence_level

    def combined(self, raw_config):
        rep = Reporting({}, None)
        rep._csv_file   = raw_config.get('csv_file',   self._csv_file)
        rep._csv_locale = raw_config.get('csv_locale', self._csv_locale)
        rep._csv_raw    = raw_config.get('csv_raw',    self._csv_raw)
        
        rep._confidence_level = raw_config.get('confidence_level',
                                               self._confidence_level)
        rep._codespeed = self._codespeed
        rep._irc       = self._irc
        rep._cli_reporter = reporter.CliReporter(rep)
        return rep

    def get_reporters(self):
        result = [self._cli_reporter]
        if self._codespeed:
            result.append(self._codespeed.get_reporter())
        if self._irc:
            result.append(self._irc.get_reporter())
        return result


class CodespeedReporting(object):

    def __init__(self, raw_config, options):
        codespeed = raw_config.get("codespeed", {})

        if options.commit_id is None:
            raise ConfigurationError("--commit-id has to be set on the command "
                                     "line for codespeed reporting.")
        self._commit_id = options.commit_id

        if options.environment is None:
            raise ConfigurationError("--environment has to be set on the "
                                     "command line for codespeed reporting.")
        self._environment = options.environment

        if "project" not in codespeed and options.project is None:
            raise ConfigurationError("The config file needs to configure a "
                                     "'project' in the reporting.codespeed "
                                     "section, or --project has to be given on "
                                     "the command line.")
        if options.project is not None:
            self._project = options.project
        else:
            self._project = codespeed["project"]

        if "url" not in codespeed:
            raise ConfigurationError("The config file needs to define a URL to "
                                     "codespeed in the reporting.codespeed "
                                     "section")
        self._url = codespeed["url"]

        self._report_incrementally = options.report_incrementally
        self._branch               = options.branch
        self._executable           = options.executable

        self._reporter = reporter.CodespeedReporter(self)

    @property
    def report_incrementally(self):
        return self._report_incrementally

    @property
    def branch(self):
        return self._branch

    @property
    def executable(self):
        return self._executable

    @property
    def project(self):
        return self._project

    @property
    def commit_id(self):
        return self._commit_id

    @property
    def environment(self):
        return self._environment

    @property
    def url(self):
        return self._url

    def get_reporter(self):
        return self._reporter


class IrcReporting(object):

    @staticmethod
    def _ensure_setting_is_present(key, config):
        if key not in config:
            raise ConfigurationError("IRC reporting needs '%s' to be set." % key)

    def __init__(self, raw_config, options):
        irc = raw_config.get("irc", {})

        self._ensure_setting_is_present('server',  irc)
        self._ensure_setting_is_present('port',    irc)
        self._ensure_setting_is_present('channel', irc)
        self._ensure_setting_is_present('nick',    irc)

        self._server  = irc['server']
        self._port    = irc['port']
        self._channel = irc['channel']
        self._nick    = irc['nick']
        self._notify  = irc.get('notify', None)

        log_events = irc.get("log_events", {})

        self._report_run_failed    = "run_failed"    in log_events
        self._report_run_completed = "run_completed" in log_events
        self._report_job_completed = "job_completed" in log_events

        self._reporter = reporter.IrcReporter(self)

    def get_reporter(self):
        return self._reporter

    @property
    def server(self):
        return self._server

    @property
    def port(self):
        return self._port

    @property
    def channel(self):
        return self._channel

    @property
    def nick(self):
        return self._nick

    @property
    def notify(self):
        return self._notify

    @property
    def report_run_failed(self):
        return self._report_run_failed

    @property
    def report_run_completed(self):
        return self._report_run_completed

    @property
    def report_job_completed(self):
        return self._report_job_completed
