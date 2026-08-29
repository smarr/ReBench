# pylint: disable=redefined-outer-name
from os import remove, environ
from os.path import dirname, join, abspath, isfile
from socket import gethostname
from subprocess import call

import pytest

from ..denoise import CommandsPaths
from ..denoise_client import exec_denoise_init
from ..model.denoise import Denoise


@pytest.fixture
def rebench_cmd():
    return CommandsPaths().absolute_path_for_command("rebench", ["--version"])


@pytest.fixture
def rebench_conf():
    return abspath(join(dirname(__file__), "..", "..", "rebench.conf"))


@pytest.fixture
def rebench_module_path():
    return abspath(join(dirname(__file__), ".."))


@pytest.fixture
def test_data_file():
    return abspath(join(dirname(__file__), "..", "test.data"))


def test_rebench(rebench_cmd, rebench_conf, rebench_module_path, test_data_file):
    assert rebench_cmd is not None

    if isfile(test_data_file):
        remove(test_data_file)

    print([rebench_cmd, rebench_conf, "e:TestRunner2"])
    return_code = call(
        [rebench_cmd, rebench_conf, "e:TestRunner2"], cwd=rebench_module_path
    )
    assert return_code == 0

    assert isfile(test_data_file)

    with open(test_data_file, "r", encoding="utf-8") as f:
        total_results = 0
        for l in f:
            if "total" in l:
                total_results += 1
        assert total_results == 80


_by_host = {
    "artemis": "sudo: a password is required",
    "gha-ubuntu": ["can_set_nice", "can_minimize_perf_sampling"],
    "gha-macos": ["can_set_nice"],
    "gha-python:3": "[Errno 2] No such file or directory: 'sudo'",
    "gha-rockylinux:10": [],
    "brutus": [
        "can_set_nice",
        "can_set_no_turbo",
        "can_set_scaling_governor",
        "can_minimize_perf_sampling",
    ],
    "cassius": "sudo: a password is required",
    "laertes": "sudo: a password is required",
    "ophelia": "sudo: a password is required",
    "zullie1": "sudo: a password is required",
}
_default_capabilities = [
    "can_set_nice",
    "can_set_shield",
    "can_set_no_turbo",
    "can_set_scaling_governor",
    "can_minimize_perf_sampling",
]


def test_machine_denoise_capabilities():
    capabilities, got_json, raw_output = exec_denoise_init(Denoise.default())
    hostname = gethostname()
    on_github_actions = environ.get("GITHUB_ACTIONS", False)
    gha_os = environ.get("RUNNER_OS", None)
    container = environ.get("CONTAINER", None)
    print("Hostname:", hostname)
    print("on_github_actions:", on_github_actions)
    print("gha_os:", gha_os)

    if container is not None:
        hostname = f"gha-{container}"
    elif on_github_actions:
        if gha_os == "Linux":
            hostname = "gha-ubuntu"
        elif gha_os == "macOS":
            hostname = "gha-macos"
        else:
            hostname = f"gha-{gha_os.lower()}"

    if hostname in _by_host:
        expectations = _by_host[hostname]
        if isinstance(expectations, str):
            assert raw_output.strip() == expectations
            expectations = None
    else:
        expectations = _default_capabilities

    if expectations is not None:
        assert isinstance(
            capabilities, dict
        ), f"Expected capabilities to be a dict, but got {capabilities}"
        for cap in expectations:
            assert cap in capabilities, (
                f"Expected {cap} to be in capabilities, but got {capabilities},"
                f" got_json: {got_json}, raw_output: {raw_output} on {hostname}"
            )
            assert (
                capabilities[cap] is True
            ), f"Expected {cap} to be True, but got {capabilities} on {hostname}"
