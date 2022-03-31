import json
import re
import sys

_re_name_and_sha = re.compile(r"^(\S+)_[0-9a-f]{40}$")


def _unmangle(method_name):
    m = _re_name_and_sha.match(method_name)
    if m:
        return m.group(1)
    return method_name


def _list_of_elem_or_str_to_json(trace):
    assert trace
    result = []
    for e in trace:
        if isinstance(e, Element):
            result.append(e.to_json())
        else:
            result.append(e)
    return result


class Element(object):

    def __init__(self, percent, method, exe_type = None, binary=None, shared_object=None):
        self.prev_divider = None
        self.trace = None
        self.percent = percent
        self.method = _unmangle(method)
        self.type = exe_type
        self.binary = binary
        self.shared_object = shared_object

    def to_json(self):
        result = {"p": self.percent, "m": self.method}
        if self.trace:
            result["t"] = _list_of_elem_or_str_to_json(self.trace)
        return result


def _create_element(m):
    percent = float(m.group(1))
    binary = m.group(2)
    shared_object = m.group(3)
    exe_type = m.group(4)
    method = m.group(5)
    top_elem = Element(percent, method, exe_type, binary, shared_object)
    return top_elem


class PerfParser(object):

    re_main_item = re.compile(r"^\s+(\d+\.\d\d)%\s\s(.+)\s\s(\S+)\s+\[(\S)]\s(\S+)$")
    re_child_divider = re.compile(r"^\s+(\|\s*)+$")

    re_child = re.compile(r"^\s+(?:\|\s*)*--(\d+\.\d\d)%--(\S+)$")
    re_stack_elements = re.compile(r"^\s+(?:\|\s+)*(?:---)?(\S+)$")

    def __init__(self, filename=None):
        self._filename = filename
        self._elements = []

    def parse_lines(self, lines):
        try:
            self._parse_lines(lines)
        except Exception as e:  # pylint: disable=broad-except
            exp_str = str(e)
            print("Failed to parse: " + exp_str)
            print("-----------perf-output------------")
            print("\n".join(lines))
            print("-----------perf-output-end--------")

    def _parse_lines(self, lines):
        top_elements = self._elements
        stack = []
        prev_divider = ""

        for line in lines:
            if not line:
                continue

            # ignore comments
            if line.startswith("#"):
                continue

            m = self.re_child_divider.match(line)
            if m:
                top_of_stack = stack[-1]

                if len(prev_divider) > len(line):
                    while (top_of_stack.prev_divider is None
                           or len(top_of_stack.prev_divider) > len(line)):
                        stack.pop()
                        top_of_stack = stack[-1]
                else:
                    top_of_stack.prev_divider = line
                prev_divider = line
                continue

            m = self.re_main_item.match(line)
            if m:
                top_elem = _create_element(m)
                top_elements.append(top_elem)
                stack = [top_elem]
                prev_divider = ""
                continue

            if len(stack) > 0:
                if line == "\n":
                    stack = []
                    prev_divider = ""
                    continue

                m = self.re_child.match(line)
                if m:
                    percent = float(m.group(1))
                    method = m.group(2)
                    elem = Element(percent, method)
                    if stack[-1].trace is None:
                        stack[-1].trace = []
                    stack[-1].trace.append(elem)
                    stack.append(elem)
                    continue

                m = self.re_stack_elements.match(line)
                if m:
                    top_of_stack = stack[-1]
                    if top_of_stack.trace is None:
                        top_of_stack.trace = []

                    stack_element = m.group(1)
                    top_of_stack.trace.append(_unmangle(stack_element))
                    continue

    def parse(self):
        with open(self._filename) as perf_file:  # pylint: disable=unspecified-encoding
            self.parse_lines(perf_file)

    def print_elements(self):
        for e in self._elements:
            print("     %.2f%%  %s  %s  [%s] %s"
                  % (e.percent, e.binary, e.shared_object, e.type, e.method))
            if e.trace:
                if isinstance(e.trace[0], Element):
                    print("            |          ")
                for i in range(len(e.trace)):  # pylint: disable=consider-using-enumerate
                    is_last = i == len(e.trace) - 1
                    self._print_child(e.trace[i], is_last, "            ")
            print("")

    def _print_child(self, e, is_last, indentation):
        if isinstance(e, Element):
            last_char = " " if is_last else " "
            print("%s%s--%.2f%%--%s" % (indentation, last_char, e.percent, e.method))
            if e.trace:
                if isinstance(e.trace[0], Element):
                    print(indentation + "           |          ")
                for i in range(len(e.trace)):  # pylint: disable=consider-using-enumerate
                    is_last = i == len(e.trace) - 1
                    self._print_child(e.trace[i], is_last, indentation + "           ")
        else:
            print(indentation + "          " + e)

    def to_json(self):
        return _list_of_elem_or_str_to_json(self._elements)

    def get_elements(self):
        return self._elements


if __name__ == "__main__":
    p = PerfParser(sys.argv[1])
    p.parse()
    print(json.dumps(p.to_json()))
    # p.print_elements()
