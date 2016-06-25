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
    
    def __init__(self, raw_config, cli_reporter, options):
        self._csv_file   = raw_config.get('csv_file',   None)
        self._csv_locale = raw_config.get('csv_locale', None)
        self._csv_raw    = raw_config.get('csv_raw',    None)
        
        if "codespeed" in raw_config and options.use_codespeed:
            self._codespeed = CodespeedReporting(raw_config, options)
        else:
            self._codespeed = None

        self._cli_reporter = cli_reporter

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
    
    def combined(self, raw_config):
        rep = Reporting({}, self._cli_reporter, None)
        rep._csv_file   = raw_config.get('csv_file',   self._csv_file)
        rep._csv_locale = raw_config.get('csv_locale', self._csv_locale)
        rep._csv_raw    = raw_config.get('csv_raw',    self._csv_raw)
        
        rep._codespeed = self._codespeed
        return rep

    def get_reporters(self):
        result = []
        if self._cli_reporter:
            result.append(self._cli_reporter)
        if self._codespeed:
            result.append(self._codespeed.get_reporter())
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
