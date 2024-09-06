from ast import Module, NodeVisitor, Name, FunctionDef, parse
from inspect import getsource
from typing import Any

import pytest

from ...model.benchmark import Benchmark
from ...model.benchmark_suite import BenchmarkSuite
from ...model.build_cmd import BuildCommand
from ...model.executor import Executor
from ...model.exp_variables import ExpVariables
from ...model.exp_run_details import ExpRunDetails
from ...model.profiler import Profiler, PerfProfiler
from ...model.run_id import RunId


class _FieldAccesses(NodeVisitor):
    def __init__(self):
        self.fields = set()

    def reset(self):
        self.fields = set()

    def visit_Attribute(self, node):
        if isinstance(node.value, Name) and node.value.id == "self":
            self.fields.add(node.attr)

        self.generic_visit(node)


def _get_ast(obj: Any) -> Module:
    source = getsource(obj)
    return parse(source)


def _get_methods(ast: Module, method_names) -> dict[str, FunctionDef]:
    result = {}

    clazz = ast.body[0]
    methods = clazz.body  # type: ignore

    for mn in method_names:
        found = False
        for m in methods:
            if not isinstance(m, FunctionDef):
                continue
            if m.name == mn:
                result[m.name] = m
                found = True
                break
        if not found:
            raise AttributeError(f"Method {mn} not found in class {clazz.name}")  # type: ignore

    return result


def _get_accessed_fields(method: FunctionDef) -> set[str]:
    visitor = _FieldAccesses()
    visitor.visit(method)
    return visitor.fields


class _P:
    def __init__(self, cls, expected_fields, additional_expected_fields=None):
        self.cls = cls
        self.method_names = ["as_dict", "__lt__", "__eq__", "__hash__"]
        self.expected_fields = expected_fields
        self.additional_expected_fields = additional_expected_fields

    def __str__(self):
        return self.cls.__name__


_SAME_FIELD_TEST_CASES = [
    _P(
        Benchmark,
        {"command", "suite", "extra_args", "run_details", "name", "variables"},
    ),
    _P(
        Executor,
        {
            "action",
            "path",
            "executable",
            "args",
            "name",
            "description",
            "build",
            "run_details",
            "variables",
        },
    ),
    _P(
        BenchmarkSuite,
        {"command", "location", "executor", "name", "build", "_desc"},
    ),
    _P(
        ExpRunDetails,
        {
            "env",
            "warmup",
            "max_invocation_time",
            "min_iteration_time",
            "invocations",
            "iterations",
            "ignore_timeouts",
            "parallel_interference_factor",
            "execute_exclusively",
            "retries_after_failure",
            "invocations_override",
            "iterations_override",
        },
    ),
    _P(
        ExpVariables,
        {"input_sizes", "cores", "variable_values", "tags"},
    ),
    _P(
        RunId,
        {"cores", "input_size", "var_value", "tag", "benchmark", "machine"},
        {"as_dict": {"cmdline", "location"}},
    ),
    _P(
        BuildCommand,
        {"command"},
        {"__lt__": {"location"}, "__eq__": {"location"}, "__hash__": {"location"}},
    ),
    _P(
        PerfProfiler,
        {"name", "record_args", "report_args"},
    ),
]


@pytest.mark.parametrize("p", _SAME_FIELD_TEST_CASES, ids=lambda p: p.cls.__name__)
def test_access_same_fields(p):
    """
    The tests here should make sure that the as_dict(), from_dict(), equal_as_part_of_run_id(),
    and less_then_as_part_of_run_id() methods use the same fields.
    """
    ast = _get_ast(p.cls)
    selected_methods = _get_methods(ast, p.method_names)

    for m_name in p.method_names:
        accessed_fields = _get_accessed_fields(selected_methods[m_name])

        accessed_fields -= {"__class__", "_hash"}
        expected_fields = p.expected_fields

        if p.additional_expected_fields and m_name in p.additional_expected_fields:
            expected_fields = expected_fields.union(
                p.additional_expected_fields[m_name]
            )
        assert accessed_fields == expected_fields, "Method " + str(m_name)


_EXP_RUN_DETAILS_DATA = {
    "env": {"a": "b"},
    "warmup": 1,
    "maxInvocationTime": 2,
    "minIterationTime": 3,
}

_PROF_DATA = [
    {"name": "perf", "record_args": "record-args", "report_args": "report-args"}
]

_VAR_DATA = {
    "input_sizes": [1, 2, 3],
    "cores": [4, 5, 6],
    "variable_values": ["a", "b", "c"],
    "tags": ["x", "y", "z"],
}

_EXECUTOR_DATA = {
    "name": "exe",
    "executable": "binary",
    "path": "/path",
    "action": "benchmark",
    "args": "a b c d",
    "desc": "test desc",
    "build": "some script\nwith multiple lines",
    "runDetails": _EXP_RUN_DETAILS_DATA,
    "variables": _VAR_DATA,
}

_BENCH_SUITE_DATA = {
    "name": "a-suite",
    "command": "a-suite-command",
    "location": "/suite-path",
    "desc": "suite-desc",
    "executor": _EXECUTOR_DATA,
    "build": "suite build script\nwith multiple lines",
}

_BENCHMARK_DATA = {
    "name": "a-name",
    "command": "a-command",
    "runDetails": _EXP_RUN_DETAILS_DATA,
    "suite": _BENCH_SUITE_DATA,
    "extra_args": "some extra args",
    "variables": _VAR_DATA,
}


_RUN_ID_DATA = {
    "benchmark": _BENCHMARK_DATA,
    "cmdline": "a-cmdline",
    "cores": 1,
    "inputSize": "an input-size",
    "varValue": "a-varval",
    "tag": "a-tag",
    "extraArgs": "some extra args",
    "location": "/suite-path",
}

_SER_TEST_CASES = [
    [ExpRunDetails, [_EXP_RUN_DETAILS_DATA]],
    [Benchmark, [_BENCHMARK_DATA]],
    [Executor, [_EXECUTOR_DATA]],
    [BenchmarkSuite, [_BENCH_SUITE_DATA]],
    [RunId, [_RUN_ID_DATA]],
    [BuildCommand, ["script", "location"]],
    [ExpVariables, [_VAR_DATA]],
    [Profiler, [_PROF_DATA]],
]


@pytest.mark.parametrize("cls, data", _SER_TEST_CASES)
def test_serialization_deserialization_and_equality(cls, data):
    obj = cls.from_dict(*data)
    if cls is Profiler:
        assert isinstance(obj, list)
        assert len(obj) == 1
        assert obj[0].as_dict() == data[0][0]
    else:
        assert obj.as_dict() == data[0]

    obj2 = cls.from_dict(*data)
    assert obj == obj2
