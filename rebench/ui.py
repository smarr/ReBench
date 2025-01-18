# Copyright (c) 2018 Stefan Marr <http://www.stefan-marr.de/>
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
import sys

from io import StringIO
from os import getcwd
from typing import Optional, TYPE_CHECKING

from humanfriendly.terminal import terminal_supports_colors, ansi_wrap, auto_encode
from humanfriendly.terminal.spinners import Spinner

if TYPE_CHECKING:
    from .model.run_id import RunId

_DETAIL_INDENT = "    "
_ERASE_LINE = "\r\x1b[2K"


def escape_braces(string):
    return string.replace("{", "{{").replace("}", "}}")


class UI(object):

    def __init__(self):
        self._verbose = True
        self._debug = True

        self._prev_run_id = None
        self._prev_cmd = None
        self._prev_cwd = None
        self._prev_env = None
        self._progress_spinner = None
        self._need_to_erase_spinner = False
        self._error_once_cache = set()

    def init(self, verbose, debug):
        self._verbose = verbose
        self._debug = debug

    def spinner_initialized(self):
        return self._progress_spinner is not None

    def init_spinner(self, total):
        self._progress_spinner = UiSpinner(label="Running Benchmarks",
                                           total=total, stream=sys.stdout)
        return self._progress_spinner

    def step_spinner(self, completed_runs, label=None):
        assert self._progress_spinner
        self._progress_spinner.step(completed_runs, label)
        self._progress_spinner.stream.flush()
        self._need_to_erase_spinner = self._progress_spinner.interactive

    def _prepare_details(self, run_id: Optional["RunId"],
                         cmd: Optional[str], cwd: Optional[str], env: Optional[dict[str, str]]):
        if not run_id and not cmd:
            return None

        # avoid duplicate details
        if run_id and run_id is self._prev_run_id:
            return None

        if cmd and cmd is self._prev_cmd:
            return None

        text = None
        if run_id:
            text = "\nExecuting run:" + run_id.as_simple_string() + "\n"

        if cmd and text:
            text += _DETAIL_INDENT + "cmd: " + cmd + "\n"
        elif cmd:
            text = "\nExecuting cmd: " + cmd + "\n"

        assert text
        if cwd:
            text += _DETAIL_INDENT + "cwd: " + cwd + "\n"
        elif run_id and run_id.location:
            text += _DETAIL_INDENT + "cwd: " + run_id.location + "\n"
        else:
            text += _DETAIL_INDENT + "cwd: " + getcwd() + "\n"

        if env:
            text += _DETAIL_INDENT + "env:\n"
            for k, v in env.items():
                text += f'{_DETAIL_INDENT}{_DETAIL_INDENT}{k}="{escape_braces(v)}"\n'

        self._prev_run_id = run_id
        self._prev_cmd = cmd
        self._prev_cwd = cwd
        self._prev_env = env

        return text

    def _output_detail_header(self, run_id: Optional["RunId"],
                              cmd: Optional[str], cwd: Optional[str],
                              env: Optional[dict[str, str]]):
        text = self._prepare_details(run_id, cmd, cwd, env)
        if text:
            self._output(text, None)

    def _erase_spinner(self):
        if self._need_to_erase_spinner:
            if self._progress_spinner and self._progress_spinner.interactive:
                sys.stdout.write(_ERASE_LINE)
            self._need_to_erase_spinner = False

    def output(self, text, *args, **kw):
        self._erase_spinner()
        auto_encode(sys.stdout, text + "\n", *args, **kw)
        sys.stdout.flush()

    def _output_on_stream(self, tmp_stream, out_stream, text, color, *args, **kw):
        if terminal_supports_colors(out_stream):
            text = ansi_wrap(text, color=color)
        auto_encode(tmp_stream, text, ind=_DETAIL_INDENT, *args, **kw)

    def _output(self, text, color, *args, **kw):
        self._erase_spinner()

        self._output_on_stream(sys.stdout, sys.stdout, text, color, *args, **kw)
        sys.stdout.flush()

    def warning(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        self._output_detail_header(run_id, cmd, cwd, env)
        self._output(text, "magenta", **kw)

    def error(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        self._output_detail_header(run_id, cmd, cwd, env)
        self._output(text, "red", **kw)

    def _is_first_error_with(self, text):
        if text not in self._error_once_cache:
            self._error_once_cache.add(text)
            return True
        return False

    def error_once(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        stream = StringIO("")
        self._output_on_stream(stream, sys.stdout, text, "red", **kw)
        stream_str = stream.getvalue()

        if self._is_first_error_with(stream_str):
            self._output_detail_header(run_id, cmd, cwd, env)
            self._output(text, "red", **kw)

    def verbose_output_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        if self._verbose:
            self._output_detail_header(run_id, cmd, cwd, env)
            self._output(text, None, faint=True, **kw)

    def verbose_error_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        if self._verbose:
            self._output_detail_header(run_id, cmd, cwd, env)
            self._output(text, "red", faint=True, **kw)

    def debug_output_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        if self._debug:
            self._output_detail_header(run_id, cmd, cwd, env)
            self._output(text, None, faint=True, **kw)

    def debug_error_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        if self._debug:
            self._output_detail_header(run_id, cmd, cwd, env)
            self._output(text, "red", faint=True, **kw)


class TestDummyUI(object):

    def init(self, _verbose, _debug):
        pass

    def spinner_initialized(self):
        pass

    def init_spinner(self, _total):
        return DummySpinner()

    def step_spinner(self, completed_runs, label=None):
        pass

    def output(self, text, **kw):
        pass

    def warning(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        pass

    def error(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        pass

    def error_once(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        pass

    def verbose_output_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        pass

    def verbose_error_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        pass

    def debug_output_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        pass

    def debug_error_info(self, text, run_id=None, cmd=None, cwd=None, env=None, **kw):
        pass


class UiSpinner(Spinner):

    def step(self, progress=0, label=None):
        if self.interactive:
            super(UiSpinner, self).step(progress, label)
            return

        assert not self.interactive
        label = label or self.label
        if not label:
            raise RuntimeError("No label set for spinner!")

        if self.total:
            label = "%s: %.2f%%\n" % (label, progress / (self.total / 100.0))
        elif self.timer and self.timer.elapsed_time > 2:
            label = "%s (%s)\n" % (label, self.timer.rounded)
        else:
            label = label + "\n"
        self.stream.write(label)
        self.counter += 1


class DummySpinner(object):

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        pass
