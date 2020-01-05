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
from ..reporter import CodespeedReporter


class Reporting(object):

    @classmethod
    def compile(cls, reporting, root_reporting, options, ui):
        if "codespeed" in reporting and options and options.use_codespeed:
            codespeed = CodespeedReporting(reporting, options, ui).get_reporter()
        else:
            codespeed = root_reporting.codespeed_reporter
        # We ignore the entry for ReBenchDB here,
        # because the configuration format does not reflect the implementation details.
        # ReBenchDB is implemented as a persistence backend to capture all measurements.

        cli_reporter = root_reporting.cli_reporter
        return Reporting(codespeed, cli_reporter)

    @classmethod
    def empty(cls, cli_reporter):
        return Reporting(None, cli_reporter)

    def __init__(self, codespeed_reporter, cli_reporter):
        self._codespeed_reporter = codespeed_reporter
        self._cli_reporter = cli_reporter

    @property
    def codespeed_reporter(self):
        return self._codespeed_reporter

    @property
    def cli_reporter(self):
        return self._cli_reporter

    def get_reporters(self):
        result = []
        if self._cli_reporter:
            result.append(self._cli_reporter)
        if self._codespeed_reporter:
            result.append(self._codespeed_reporter)
        return result


class CodespeedReporting(object):

    def __init__(self, raw_config, options, ui):
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
        self._branch = options.branch
        self._executable = options.executable

        self._reporter = CodespeedReporter(self, ui)

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
