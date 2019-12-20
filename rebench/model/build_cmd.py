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


class BuildCommand(object):

    @classmethod
    def create_commands(cls, commands, build_commands, location):
        if not commands:
            return None

        return [BuildCommand.create(cmd, build_commands, location) for cmd in commands]

    @classmethod
    def create(cls, cmd, build_commands, location):
        assert cmd

        build_command = BuildCommand(cmd, location)
        if build_command in build_commands:
            return build_commands[build_command]
        return build_command

    def __init__(self, cmd, location):
        self._cmd = cmd
        self._location = location
        self._built = False
        self._build_failed = False

    @property
    def command(self):
        return self._cmd

    @property
    def location(self):
        return self._location

    @property
    def is_built(self):
        return self._built

    @property
    def is_failed_build(self):
        return self._build_failed

    def mark_succeeded(self):
        self._built = True

    def mark_failed(self):
        self._build_failed = True

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self._cmd == other._cmd and
                self._location == other._location)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._cmd, self._location))

    def as_dict(self):
        result = dict()
        result['cmd'] = self._cmd
        result['location'] = self._location
        return result
