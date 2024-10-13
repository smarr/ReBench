# Denoise

To configure a system for benchmarking, ReBench provides the `rebench-denoise` tool.
It adjusts the system settings to reduce interference by:

 - raising the process priority to minimize the impact of the process scheduler 
 - using CPU core shielding to minimize interference from other processes
 - requesting the system to avoid tubo-boosting to keep the CPU at a constant frequency
 - requesting the system to use a performance governor, which tries to keep the CPU at a high frequency
 - reducing the frequency with which perf events can be collected, except when in profiling mode

`rebench-denoise` is usually used implicitly by ReBench. Though, when using it directly,
the following four commands are important:

 - `init` checks which system settings can be adjusted and prints the current settings
 - `minimize` sets the system to reduce noise
 - `exec` executes a command with the adjusted system settings
 - `restore` sets the system back to the assumed or provided original settings

The commands are split into `minimize`, `exec`, and `restore` since some settings
are global and persist between different benchmark executions. Other commands,
for instance `nice`, which adjusts the process priority, work however directly
on the benchmark command.

The command-line interface is designed to report errors when requested or rather
implicitly enabled settings cannot be applied. Thus, it is advisable to run `init` first
to check which settings can be adjusted and then disable the options on `minimize` and `exec`
that are not supported.

A common session would look like this:

```bash
sudo rebench-denoise --num-cores 8 --cset-path /usr/bin/cset init
sudo rebench-denoise --num-cores 8 --cset-path /usr/bin/cset minimize
sudo rebench-denoise --num-cores 8 --cset-path /usr/bin/cset exec -- ./my-benchmark1 --my-args
sudo rebench-denoise --num-cores 8 --cset-path /usr/bin/cset exec -- ./my-benchmark2 --my-args
sudo rebench-denoise --num-cores 8 --cset-path /usr/bin/cset restore
```


`rebench-denoise` is a command-line tool, and supports the `--help` argument
for a brief overview of its options.

```
$ rebench-denoise --help 
usage: rebench-denoise rebench-denoise [-h] [--version] [--json]
                       [-N] [-S] [-T] [-G] [-P]
                       [-p]
                       [--cset-path CSET_PATH] [--num-cores NUM_CORES]
                       command

positional arguments:
  command              `init`|`minimize`|`restore`|`exec -- `|`kill pid`|`test`:
                          `init` determines initial settings and capabilities.
                          `minimize` sets system to reduce noise.
                          `restore` sets system to the assumed original settings.
                          `exec -- ` executes the given command with arguments.
                          `kill pid` send kill signal to the process with given id and all child processes.
                          `test` executes a computation for 20 seconds in parallel. It is only useful to test rebench-denoise itself.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --json                Output results as JSON for processing
  -N, --without-nice    Don't try setting process niceness
  -S, --without-shielding
                        Don't try shielding cores
  -T, --without-no-turbo
                        Don't try setting no_turbo
  -G, --without-scaling-governor
                        Don't try setting scaling governor
  -P, --without-min-perf-sampling
                        Don't try to minimize perf sampling
  -p, --for-profiling   Don't restrict CPU usage by profiler
  --cset-path CSET_PATH
                        Absolute path to cset. Needed for `init`, `minimize`, and `restore`.
  --num-cores NUM_CORES
                        Number of cores. Needed for `init`, `minimize`, and `restore`.
```

## Core Shielding

For shielding cores from other processes, `rebench-denoise` uses the `cset` tool.
Since `rebench-denoise` is usually executed with `sudo`, the path to the `cset` tool
needs to be provided explicitly.

Denoise determines a set of cores to be used for benchmarking based on the number of
cores that is configured with the `--num-cores` option.

The set of cores is communicated to the benchmarked process by setting the `REBENCH_DENOISE_CORE_SET`
environment variable. This allows the benchmarked process to bind know which cores can be used.
