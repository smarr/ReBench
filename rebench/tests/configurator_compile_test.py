# pylint: disable=redefined-outer-name
import pytest

from ..configurator import validate_config, Configurator
from ..persistence import DataStore
from ..ui import TestDummyUI


# precedence order/priority, from most important to least important:
CONFIG_ELEMENTS = [
    "benchmark",
    "benchmark suite",
    "executor",
    "experiment",
    "experiments",
    "runs",
    "machine",
]


def create_list_of_pairs_to_check():
    result = set()
    for i, high in enumerate(CONFIG_ELEMENTS):
        for j, low in enumerate(CONFIG_ELEMENTS):
            if i < j:
                result.add((high, low))
    return result


def test_precedence_order_pairs():
    pairs = create_list_of_pairs_to_check()
    assert len(pairs) == 21


# the run details, with a low priority [0] and a high priority [1] setting
RUN_DETAILS = {
    "invocations": [11, 22],
    "iterations": [33, 44],
    "warmup": [3, 5],
    "min_iteration_time": [100, 200],
    "max_invocation_time": [1000, 2000],
    "ignore_timeouts": [True, False],
    "retries_after_failure": [8, 9],
    "env": [{"MY_VAR": "value"}, {"MY_VAR": "value2"}],
    "denoise": [{"use_nice": True}, {"use_nice": False}],
}

# the variables, with a low priority [0] and a high priority [1] setting
VARIABLES = {
    "input_sizes": [[100], [300]],
    "cores": [[5], [7]],
    "variable_values": [["lowVar"], ["highVar"]],
    "tags": [["lowTag"], ["highTag"]],
}


@pytest.fixture
def ui():
    return TestDummyUI()


@pytest.fixture
def data_store(ui):
    return DataStore(ui)


def create_raw_configuration():
    return {
        "benchmark_suites": {
            "TestSuite": {
                "gauge_adapter": "test",
                "command": "cmd",
                "benchmarks": [
                    {"Bench1": {}},
                ],
            }
        },
        "machines": {"testMachine": {}},
        "executors": {"TestExec": {"path": "path", "executable": "exec"}},
        "experiments": {
            "testExp": {"suites": ["TestSuite"], "executions": [{"TestExec": {}}]}
        },
    }


def add_setting(config, elem_name, key, value):
    if elem_name == "benchmark":
        config["benchmark_suites"]["TestSuite"]["benchmarks"][0]["Bench1"][key] = value
    elif elem_name == "benchmark suite":
        config["benchmark_suites"]["TestSuite"][key] = value
    elif elem_name == "executor":
        config["executors"]["TestExec"][key] = value
    elif elem_name == "experiment":
        config["experiments"]["testExp"]["executions"][0]["TestExec"][key] = value
    elif elem_name == "experiments":
        config["experiments"]["testExp"][key] = value
    elif elem_name == "runs":
        config["runs"] = {key: value}
    elif elem_name == "machine":
        config["machines"]["testMachine"][key] = value


def create_test_input():
    result = []
    for highElem, lowElem in create_list_of_pairs_to_check():
        for key, value in RUN_DETAILS.items():
            result.append((highElem, lowElem, key, value[1], value[0]))
        if highElem != "runs" and lowElem != "runs":
            # runs do not have EXP_VARIABLES, it's inconsistent,
            # but also not obviously wrong
            for key, value in VARIABLES.items():
                result.append((highElem, lowElem, key, value[1], value[0]))
    return result


def create_config(high_elem, low_elem, val_key, high_val, low_val):
    raw_config = create_raw_configuration()
    add_setting(raw_config, high_elem, val_key, high_val)
    add_setting(raw_config, low_elem, val_key, low_val)
    return raw_config


@pytest.mark.parametrize(
    "high_elem, low_elem, val_key, high_val, low_val", create_test_input()
)
def test_generated_config_is_valid(high_elem, low_elem, val_key, high_val, low_val):
    raw_config = create_config(high_elem, low_elem, val_key, high_val, low_val)
    assert raw_config is not None
    validate_config(raw_config)


@pytest.mark.parametrize(
    "high_elem, low_elem, val_key, high_val, low_val", create_test_input()
)
def test_experiment_with_higher_priority_setting(
    ui, data_store, high_elem, low_elem, val_key, high_val, low_val
):
    raw_config = create_config(high_elem, low_elem, val_key, high_val, low_val)
    assert_expected_value_in_config(ui, data_store, raw_config, val_key, high_val)


def assert_expected_value_in_config(ui, data_store, raw_config, val_key, high_val):
    cnf = Configurator(raw_config, data_store, ui, machine="testMachine")
    runs = list(cnf.get_runs())
    assert len(runs) == 1

    run = runs[0]

    # need to do just a little bit of mapping
    # the names are not a 1:1 match, and some of the lists will turn into distinct runs
    if val_key == "warmup":
        val_key = "warmup_iterations"
    elif val_key == "input_sizes":
        val_key = "input_size"
        high_val = high_val[0]
    elif val_key == "cores":
        high_val = high_val[0]
    elif val_key == "variable_values":
        val_key = "var_value"
        high_val = high_val[0]
    elif val_key == "tags":
        val_key = "tag"
        high_val = high_val[0]
    elif val_key == "denoise":
        assert run.denoise.use_nice == high_val["use_nice"]
        return

    assert getattr(run, val_key) == high_val


def create_machine_test_input():
    result = []

    for key, value in RUN_DETAILS.items():
        result.append((key, value[1]))

    for key, value in VARIABLES.items():
        result.append((key, value[1]))
    return result


@pytest.mark.parametrize("key, value", create_machine_test_input())
def test_machine_settings_being_used(ui, data_store, key, value):
    raw_config = create_raw_configuration()
    add_setting(raw_config, "machine", key, value)

    assert_expected_value_in_config(ui, data_store, raw_config, key, value)
