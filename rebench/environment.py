import getpass
import os
import subprocess

from cpuinfo import get_cpu_info
from psutil import virtual_memory


try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2.7
    from urlparse import urlparse


def _encode_str(out):
    as_string = out.decode('utf-8')
    if as_string and as_string[-1] == '\n':
        as_string = as_string[:-1]
    return as_string


def _exec(cmd):
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return None
    return _encode_str(out)


def determine_source_details():
    result = dict()
    try:
        repo_url = subprocess.check_output(['git', 'ls-remote', '--get-url'])
    except subprocess.CalledProcessError:
        repo_url = ''

    parsed = urlparse(repo_url)
    if parsed.password:
        # remove password
        parsed = parsed._replace(
            netloc="{}@{}".format(parsed.username, parsed.hostname))
    result['repoURL'] = _encode_str(parsed.geturl())

    result['branchOrTag'] = _exec(['git', 'show', '-s', '--format=%D', 'HEAD'])
    result['commitId'] = _exec(['git', 'rev-parse', 'HEAD'])
    result['commitMsg'] = _exec(['git', 'show', '-s', '--format=%B', 'HEAD'])
    result['authorName'] = _exec(['git', 'show', '-s', '--format=%aN', 'HEAD'])
    result['committerName'] = _exec(['git', 'show', '-s', '--format=%cN', 'HEAD'])
    result['authorEmail'] = _exec(['git', 'show', '-s', '--format=%aE', 'HEAD'])
    result['committerEmail'] = _exec(['git', 'show', '-s', '--format=%cE', 'HEAD'])
    return result


def determine_environment():
    result = dict()
    result['userName'] = getpass.getuser()
    result['manualRun'] = not ('CI' in os.environ and os.environ['CI'] == 'true')

    u_name = os.uname()
    result['hostName'] = u_name[1]
    result['osType'] = u_name[0]
    cpu_info = get_cpu_info()
    result['cpu'] = cpu_info['brand_raw']
    result['clockSpeed'] = (cpu_info['hz_advertised'][0]
                            * (10 ** cpu_info['hz_advertised'][1]))
    result['memory'] = virtual_memory().total
    result['software'] = []
    result['software'].append({'name': 'kernel', 'version': u_name[3]})
    result['software'].append({'name': 'kernel-release', 'version': u_name[2]})
    result['software'].append({'name': 'architecture', 'version': u_name[4]})
    return result
