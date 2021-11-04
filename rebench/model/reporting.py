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
        if "codespeed" in reporting and options and options.use_data_reporting:
            codespeed = CodespeedReporting(reporting, options, ui).reporter
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
        self.codespeed_reporter = codespeed_reporter
        self.cli_reporter = cli_reporter

    def get_reporters(self):
        result = []
        if self.cli_reporter:
            result.append(self.cli_reporter)
        if self.codespeed_reporter:
            result.append(self.codespeed_reporter)
        return result


class CodespeedReporting(object):

    def __init__(self, raw_config, options, ui):
        codespeed = raw_config.get("codespeed", {})

        if options.commit_id is None:
            raise ConfigurationError("--commit-id has to be set on the command "
                                     "line for codespeed reporting.")
        self.commit_id = options.commit_id

        if options.environment is None:
            raise ConfigurationError("--environment has to be set on the "
                                     "command line for codespeed reporting.")
        self.environment = options.environment

        if "project" not in codespeed and options.project is None:
            raise ConfigurationError("The config file needs to configure a "
                                     "'project' in the reporting.codespeed "
                                     "section, or --project has to be given on "
                                     "the command line.")
        if options.project is not None:
            self.project = options.project
        else:
            self.project = codespeed["project"]

        if "url" not in codespeed:
            raise ConfigurationError("The config file needs to define a URL to "
                                     "codespeed in the reporting.codespeed "
                                     "section")
        self.url = codespeed["url"]

        self.report_incrementally = options.report_incrementally
        self.branch = options.branch
        self.executable = options.executable

        self.reporter = CodespeedReporter(self, ui)
