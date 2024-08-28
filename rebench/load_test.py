import sys

from argparse import ArgumentParser
from ctypes import c_ulonglong
from multiprocessing import Process, Value
from time import perf_counter, sleep

try:
    from . import __version__ as rebench_version
except (ValueError, ImportError):
    rebench_version = "unknown"

def load_test(duration, val):
    start_time = perf_counter()
    counter = 0
    while perf_counter() - start_time < duration:
        counter += 1
    val.value = counter


def _create_process_and_value(duration):
    val = Value(c_ulonglong, 0)
    p = Process(target=load_test, args=[duration, val])
    return val, p


def start_load_test(args):
    vals_and_procs = [_create_process_and_value(args.duration) for _ in range(args.num_cores)]

    for vp in vals_and_procs:
        if args.staggered:
            sleep(1)
        vp[1].start()

    for vp in vals_and_procs:
        vp[1].join()

    return [v.value for v, _ in vals_and_procs]


def _shell_options():
    parser = ArgumentParser()
    parser.add_argument('--version', action='version',
                        version="%(prog)s " + rebench_version)
    parser.add_argument('--num-cores', dest='num_cores', type=int, default=1,
                        help='Number of cores to use. Default: 1')
    parser.add_argument('--duration', dest='duration', type=int, default=10,
                        help='Duration of the test in seconds. Default: 10')
    parser.add_argument('--staggered', dest='staggered', action='store_true',
                        default=False,
                        help='Use staggered start of the workers, with a 1s delay between each')
    return parser


def main_func():
    arg_parser = _shell_options()
    args, remaining_args = arg_parser.parse_known_args()

    values = start_load_test(args)
    output_report(values)


def output_report(values):
    highest = max(values)

    for v in values:
        print(f"Value:\t{v}\tpercentage:\t{v/highest*100:.2f}%")


if __name__ == "__main__":
    sys.exit(main_func())
