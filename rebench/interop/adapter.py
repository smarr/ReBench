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
import re
import pkgutil
import sys
from os.path import join


class GaugeAdapter(object):
    """A GaugeAdapter implements a common interface to evaluate the output of
       benchmarks and to determine measured performance values.
       The GaugeAdapter class also provides some basic helper functionality.
    """

    # definition of some regular expression to identify erroneous runs
    re_error = re.compile("Error")
    re_segfault = re.compile("Segmentation fault")
    re_bus_error = re.compile("Bus error")

    def __init__(self, include_faulty, executor):
        self._include_faulty = include_faulty
        self._other_error_definitions = None
        self._executor = executor

    def acquire_command(self, run_id):
        return run_id.cmdline_for_next_invocation()

    def parse_data(self, data, run_id, invocation):
        raise NotImplementedError()

    def check_for_error(self, line):
        """Check whether the output line contains one of the common error
           messages. If it's an erroneous run, the result has to be discarded.
        """
        if self._include_faulty:
            return False

        if self.re_error.search(line):
            return True
        if self.re_segfault.search(line):
            return True
        if self.re_bus_error.search(line):
            return True

        if self._other_error_definitions:
            for reg_ex in self._other_error_definitions:
                if reg_ex.search(line):
                    return True

        return False


class ExecutionDeliveredNoResults(Exception):
    """The exception to be raised when no results were obtained from the given
       data string."""
    def __init__(self, unparsable_data):
        super(ExecutionDeliveredNoResults, self).__init__()
        self._unparseable_data = unparsable_data


class OutputNotParseable(ExecutionDeliveredNoResults):
    pass


class ResultsIndicatedAsInvalid(ExecutionDeliveredNoResults):
    pass


def instantiate_adapter(adapter_cfg, include_faulty, executor):
    if isinstance(adapter_cfg, str):
        return _search_in_rebench_modules(adapter_cfg, include_faulty, executor)
    return _load_directly(adapter_cfg, include_faulty, executor)


def _search_in_rebench_modules(name, include_faulty, executor):
    adapter_name = name + "Adapter"
    root = sys.modules['rebench.interop'].__path__

    for _, module_name, _ in pkgutil.walk_packages(root):
        # depending on how ReBench was executed, name might one of the two
        try:
            mod = __import__("rebench.interop." + module_name, fromlist=adapter_name)
        except ImportError:
            try:
                mod = __import__("interop." + module_name, fromlist=adapter_name)
            except ImportError:
                mod = None
        adapter_cls = _get_adapter_case_insensitively_from_module(mod, adapter_name)
        if adapter_cls is not None:
            return adapter_cls(include_faulty, executor)

    return None


def _get_adapter_case_insensitively_from_module(mod, adapter_name):
    if mod is not None:
        keys = mod.keys() if isinstance(mod, dict) else dir(mod)
        for key in keys:
            if key.lower() == adapter_name.lower():
                return mod[key] if isinstance(mod, dict) else getattr(mod, key)
    return None


def _load_directly(adapter_cfg, include_faulty, executor):
    name, path = next(iter(adapter_cfg.items()))
    full_path = join(executor.config_dir, path)
    with open(full_path, 'r') as adapter_file:  # pylint: disable=unspecified-encoding
        file_content = adapter_file.read()

    module_globals = {'__name__': name}
    code = compile(file_content, full_path, 'exec')
    exec(code, module_globals)  # pylint: disable=exec-used

    cls = _get_adapter_case_insensitively_from_module(module_globals, name)
    if cls is not None:
        return cls(include_faulty, executor)
    return None
