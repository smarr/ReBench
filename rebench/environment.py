import getpass
import os
import subprocess

from urllib.parse import urlparse
from cpuinfo.cpuinfo import _get_cpu_info_internal
from psutil import virtual_memory

from .subprocess_with_timeout import output_as_str


def _encode_str(out):
    as_string = output_as_str(out)
    if as_string and as_string[-1] == '\n':
        as_string = as_string[:-1]
    return as_string


def _exec(cmd):
    try:
        with open(os.devnull, 'w') as dev_null_f:  # pylint: disable=unspecified-encoding
            out = subprocess.check_output(cmd, stderr=dev_null_f)
    except subprocess.CalledProcessError:
        return None
    return _encode_str(out)


_source = None


def extract_base(branch_or_tag):
    # in local working copies things may look like HEAD -> branch, remote/branch, otherBranch
    if ',' in branch_or_tag:
        branch_or_tag = branch_or_tag.split(',')[0]

    return branch_or_tag.replace('HEAD -> ', '')


def git_not_available():
    return _exec(['git', '--version']) is None


def git_repo_not_initialized():
    return _exec(['git', 'rev-parse']) is None


def determine_source_details(configurator):
    global _source  # pylint: disable=global-statement
    if _source:
        return _source

    result = {}
    git_cmd = ['git']
    if configurator and configurator.options and configurator.options.git_repo:
        git_cmd += ['-C', configurator.options.git_repo]

    is_git_repo = _exec(git_cmd + ['rev-parse']) is not None
    if not is_git_repo:
        result['repoURL'] = None
        result['branchOrTag'] = None
        result['commitId'] = None
        result['commitMsg'] = None
        result['authorName'] = None
        result['committerName'] = None
        result['authorEmail'] = None
        result['committerEmail'] = None
        _source = result
        return result

    repo_url = _exec(git_cmd + ['ls-remote', '--get-url']) if is_git_repo else None
    if repo_url is None:
        repo_url = ''

    parsed = urlparse(repo_url)
    if parsed.password:
        # remove password
        parsed = parsed._replace(
            netloc="{}@{}".format(parsed.username, parsed.hostname))
    result['repoURL'] = _encode_str(parsed.geturl())

    result['branchOrTag'] = extract_base(_exec(git_cmd + ['show', '-s', '--format=%D', 'HEAD']))
    result['commitId'] = _exec(git_cmd + ['rev-parse', 'HEAD'])
    result['commitMsg'] = _exec(git_cmd + ['show', '-s', '--format=%B', 'HEAD'])
    result['authorName'] = _exec(git_cmd + ['show', '-s', '--format=%aN', 'HEAD'])
    result['committerName'] = _exec(git_cmd + ['show', '-s', '--format=%cN', 'HEAD'])
    result['authorEmail'] = _exec(git_cmd + ['show', '-s', '--format=%aE', 'HEAD'])
    result['committerEmail'] = _exec(git_cmd + ['show', '-s', '--format=%cE', 'HEAD'])

    _source = result
    return result


_environment = None


def init_env_for_test():
    global _environment  # pylint: disable=global-statement
    _environment = {
        'hostName': 'test',
        'userName': 'test'
    }


def init_environment(denoise_result, ui):
    u_name = os.uname()
    result = {
        'userName': getpass.getuser(),
        'manualRun': not ('CI' in os.environ and os.environ['CI'] == 'true'),
        'hostName': u_name[1],
        'osType': u_name[0],
        'memory': virtual_memory().total,
        'denoise': {} if denoise_result is None else denoise_result.details
    }

    try:
        cpu_info = _get_cpu_info_internal()
        if cpu_info:
            result['cpu'] = cpu_info['brand_raw']
            if 'hz_advertised' in cpu_info:
                result['clockSpeed'] = (cpu_info['hz_advertised'][0]
                                        * (10 ** cpu_info['hz_advertised'][1]))
            else:
                result['clockSpeed'] = 0
    except ValueError:
        pass

    if 'cpu' not in result:
        ui.warning('Was not able to determine the type of CPU used and its clock speed.'
                   + ' Thus, these details will not be recorded with the data.')

    result['software'] = []
    result['software'].append({'name': 'kernel', 'version': u_name[3]})
    result['software'].append({'name': 'kernel-release', 'version': u_name[2]})
    result['software'].append({'name': 'architecture', 'version': u_name[4]})

    global _environment  # pylint: disable=global-statement
    _environment = result


def determine_environment():
    global _environment  # pylint: disable=global-statement,global-variable-not-assigned
    if _environment:
        return _environment

    raise RuntimeError("Environment was not initialized before accessing it.")
