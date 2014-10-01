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
from . import value_with_optional_details
import logging


class BenchmarkConfig(object):
    _registry = {}
    
    @classmethod
    def reset(cls):
        cls._registry = {}
    
    @classmethod
    def get_config(cls, name, vm_name, suite_name, extra_args, warmup):
        key = (name, vm_name, suite_name,
               '' if extra_args is None else str(extra_args),
               str(warmup))

        if key not in BenchmarkConfig._registry:
            raise ValueError("Requested configuration is not available: " +
                             key.__str__())

        return BenchmarkConfig._registry[key]
    
    @classmethod
    def compile(cls, bench, suite):
        """Specialization of the configurations which get executed by using the
           suite definitions.
        """
        name, details = value_with_optional_details(bench, {})

        command            = details.get('command', name)

        # TODO: remove in ReBench 1.0
        if 'performance_reader' in details:
            logging.warning("Found deprecated 'performance_reader' key in"
                            " configuration, please replace by 'gauge_adapter'"
                            " key.")
            details['gauge_adapter'] = details['performance_reader']

        gauge_adapter      = details.get('gauge_adapter',
                                         suite.gauge_adapter)
        extra_args         = details.get('extra_args', None)
        codespeed_name     = details.get('codespeed_name', None)
        warmup             = int(details.get('warmup',        0))
        return BenchmarkConfig(name, command, gauge_adapter, suite,
                               suite.vm, extra_args, warmup, codespeed_name)

    @classmethod
    def _register(cls, cfg):
        key = tuple(cfg.as_str_list())
        if key in BenchmarkConfig._registry:
            raise ValueError("Two identical BenchmarkConfig tried to register. "
                             + "This seems to be wrong.")
        else:
            BenchmarkConfig._registry[key] = cfg
        return cfg
    
    def __init__(self, name, command, gauge_adapter, suite, vm, extra_args,
                 warmup, codespeed_name):
        self._name               = name
        self._command            = command
        self._extra_args         = extra_args
        self._codespeed_name     = codespeed_name
        self._warmup             = warmup
        self._gauge_adapter      = gauge_adapter
        self._suite = suite

        self._vm = vm
        self._runs = set()      # the compiled runs, these might be shared
                                # with other benchmarks/suites
        self._register(self)
    
    def add_run(self, run):
        self._runs.add(run)
    
    @property
    def name(self):
        return self._name

    @property
    def command(self):
        """
        We distinguish between the benchmark name, used for reporting, and the
        command that is passed to the benchmark executor.
        If no command was specified in the config, the name is used instead.
        See the compile(.) method for details.

        :return: the command to be passed to the benchmark invocation
        """
        return self._command

    @property
    def codespeed_name(self):
        return self._codespeed_name
    
    @property
    def extra_args(self):
        return self._extra_args

    @property
    def warmup_iterations(self):
        return self._warmup
    
    @property
    def gauge_adapter(self):
        return self._gauge_adapter
    
    @property
    def suite(self):
        return self._suite
    
    @property
    def vm(self):
        return self._vm

    @property
    def execute_exclusively(self):
        return self._vm.execute_exclusively
    
    def __str__(self):
        return "%s, vm:%s, suite:%s, args:'%s', warmup: %d" % (
            self._name, self._vm.name, self._suite.name, self._extra_args or '',
            self._warmup)
    
    def as_simple_string(self):
        if self._extra_args:
            return "%s (%s, %s, %s, %d)"  % (self._name, self._vm.name,
                                             self._suite.name, self._extra_args,
                                             self._warmup)
        else:
            return "%s (%s, %s, %d)" % (self._name, self._vm.name,
                                        self._suite.name, self._warmup)
        
    def as_str_list(self):
        return [self._name, self._vm.name, self._suite.name,
                '' if self._extra_args is None else str(self._extra_args),
                str(self._warmup)]

    @classmethod
    def from_str_list(cls, str_list):
        return cls.get_config(str_list[0], str_list[1], str_list[2],
                              None if str_list[3] == '' else str_list[3],
                              int(str_list[4]))
