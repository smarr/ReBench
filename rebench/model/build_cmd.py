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
from typing import Optional, Mapping


class BuildCommand(object):

    @classmethod
    def create(cls, commands: Optional[list[str]], location: Optional[str],
               deduplicated_build_commands: Mapping["BuildCommand", "BuildCommand"]
               ) -> Optional["BuildCommand"]:
        if not commands:
            return None

        command = "\n".join(commands)

        build_command = BuildCommand(command, location)
        if build_command in deduplicated_build_commands:
            return deduplicated_build_commands[build_command]
        return build_command

    def __init__(self, cmd, location):
        self.command = cmd
        self.location = location
        self.is_built = False
        self.build_failed = False

    def mark_succeeded(self):
        self.is_built = True

    def mark_failed(self):
        self.build_failed = True

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.command == other.command and
                self.location == other.location)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.command, self.location))

    def as_dict(self):
        return {
            'cmd': self.command,
            'location': self.location
        }
