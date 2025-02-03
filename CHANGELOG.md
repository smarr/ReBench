# Change Log

## [Unreleased]

## [1.3.0] Env Vars part of RunId, and Support for Machine-Specific Settings - 2025-02-03

This release has three major changes that will affect how ReBench interprets configurations,
and a change for `denoise` that requires an update of the `sudoers` file.

### 1. "Run" identity is now based on all details, e.g. also env vars (#271)

This change can affect the number of different runs ReBench identifies.
Until now, the identity of a "run" was based on the command line generated from the
configuration. However, this meant, we could not distinguish between runs
with for instance different environment variables.
From now on, the identity of runs is based on all details of the configuration,
which may mean that configuration files may result in more distinct runs
than they did previously.

### 2. Build commands are combined and run as a single shell script (#269)

The `build:` key takes a list of commands, which are now combined into a single
shell script. Previously, each command was run separately. 
Since we avoid executing the same command multiple times,
treating commands separately led to confusing results and was not very useful.
By combining the commands into a single script, identifying redundant script
execution leads to more predictable results.

### 3. Support for machine-specific settings (#272)

A new lowest-priority configuration level is introduced, which is meant to define
machine-specific settings. This can be useful, for instance for settings like this:

```yaml
machines:
  smaller-machine:
    cores: [1, 2]
  larger-machine:
    cores: [1, 2, 4, 8]
```

These settings are combined into a configuration based on the usual rules.
So, if a benchmark suite or a benchmark give specific values for `cores:`, these
have higher priority. However, one would likely use it, avoiding
benchmark-specific values.

When executing ReBench on the corresponding machine, these settings can be
selected with the `-m` option. Thus, the larger machine configuration is used
when running:

```bash
rebench -m larger-machine rebench.conf
```

### 4. `rebench` uses `denoise.py` directly as script (#281)

Previously, we used the `rebench-denoise` script that is automatically created
during the setup process. However, this required a setup where ReBench was
installed so that the root user had access to it with a proper `PYTHONPATH`.
To avoid issues with setup, avoid having to pass `PYTHONPATH` through `sudo`,
and to make the use of denoise more robust, we changed `denoise.py` so that it
can be used directly as a script by ReBench.

In practice, the means, it's likely that the `sudoers` file will need to be
updated to point to the `denoise.py` script directly. ReBench will output the
path to the script when it is not able to use it directly.


### Other Minor Changes

#### Features
 - add support for ReBenchDB API Version 2 (#236)
 - expand `~` in paths, right before invocation (#240, #283)
 - add summary for columns where all values are the same (#256)
 - show `env` in debug output (#280)

#### Changes
 - make output for currently running benchmark more compact (#237)
 - invoke denoise with absolute path to avoid need for having it on a secure_path (#238, #273)
 - rename the machines variable/filters to a tags variable/filter (#264)
 - support Python 3.13 as latest version, drop support for Python 3.8 (#268)
 - reduce number of git invocations to get source information (#275)
 - distinguish `rebench` return codes for different errors (#282)

#### Bug Fixes
 - added missing machine column heading for summary table (#246)
 - behave more gracefully on bare-bone setup, e.g. without git (#245)
 - raise error in `TimeAdapter` to match other adapters (#254)
 - make profiling with `perf` more robust (#255)
 - make denoise more robust to absent tools and running as root with a user-level installation (#260)
 - fix handling of ctrl-c interrupts (#262)
 - avoid unnecessary warning about data reporting, when no data is to be reported (#277)

#### Development
 - use black formatting (#267)
 - use mypy type checking and add some annotations (#270)
 - use `pip install —editable` in CI to avoid incorrect coverage reporting (#279)
 - add testing on Rocky Linux with integration test (#282)

Thanks to @antonzhukovin, @vext01, and @martinmcclure for their contributions!

**Full Changelog**: https://github.com/smarr/ReBench/compare/v1.2.0...v1.3.0

## [1.2.0] Custom Gauge Adapters - 2023-08-06

The main feature of this release is the new support for custom
gauge adapters. This allows the use of a Python file from the
ReBench config, which can parse arbitrary output from a benchmark, see #209.

Furthermore, ReBench dropped support for Python 2. If you require ReBench to
run with Python 2, please see #208 for the removed supported code, or use
version 1.1.0, which was the last version with Python 2 support.


Other new features:
 - add command-line option `-D` to disable the use of denoise (#217)
 - include CSV headers into .data files (#220, #227)
 - abort all benchmarks for which the exector is missing (#224)
 - make the current invocation accessible in the command as `%(invocation)s` (#230)

Other changes:
 - make sure `null` is not reported as `'None'` to ReBenchDB (#232)
 - fix handling of environment variables when sudo is used (#210)
 - try `gtime` from MacPorts as alternative `time` command on macOS (#212)
 - update py-cpuinfo to work on macOS with ARM-base CPUs (#212)
 - make error more readable when executor is not available (#213)
 - add testing on macOS on Github Actions (#226)

Thanks to @naomiGrew for the contributions!

**Full Changelog**: https://github.com/smarr/ReBench/compare/v1.1.0...v1.2.0

## [1.1.0] Denoise - 2023-02-21

This release focuses on reducing the noise from the system  (#143, #144).
For this purpose, it introduces the `rebench-denoise` tool, which will adapt
system parameters to:

- change CPU governor to the performance setting
- disables turbo boost
- reduces the sampling frequency allowed by the kernel
- execute benchmarks with CPU shielding and `nice -n-20`

`rebench-denoise` can also be used as stand-alone tool, is documented here:
https://rebench.readthedocs.io/en/latest/denoise/

The use of `rebench-denoise` will require root rights.

Other new features include:

 - add support for configuring environment variables (#174)
 - add support for recording profiling information (#190)
 - add support for printing the execution plan without running it (#171)
 - add marker in configuration to make setting important, which overrides
   previous settings, giving more flexibility in composing
   configuration values (#170)
 - add support for filtering experiments by machines (#161)

Thanks to @tobega, @qinsoon, @cmccandless, @OctaveLarose, and @raehik for their contributions.

Other notable improvements:

 - `-R` now disables data reporting, replacing the previous `-S` (#145)
 - added support to report experiment completion to ReBenchDB (#149)
 - fixed JMH support (#147)
 - fixed string/byte encoding issues between Python 2 and 3 (#142)
 - updated py-cpuinfo (#137, #138, #141)
 - allow the use of float values in the ReBenchLogAdapter parser (#201)
 - make gauge adapter names in configurations case-insensitive (#202)
 - improve documentation (#197, #198)
 - use PyTest for unit tests (#192)

**Full Changelog**: https://github.com/smarr/ReBench/compare/v1.0.1...v1.1.0


## [1.0.1] - 2020-06-23

This is a bug fix release.

 - adopt py-cpuinfo 6.0.0 and pin version to avoid issues with changing APIs (#138)
   Thanks to @tobega for the fix!

## [1.0.0] Foundations - 2020-05-02

This is the first official release of ReBench as a "feature-complete" product.
Feature-complete here means, it is a tried and tested tool for benchmark
execution. It is highly
[configurable](https://rebench.readthedocs.io/en/latest/config/),
[documented](https://rebench.readthedocs.io/en/latest/),
and [successfully used](https://github.com/smarr/ReBench#use-in-academia).

This 1.0 release does not signify any new major features, but instead marks a
point where ReBench has been stable and relieable for a long time.

ReBench is designed to

 - enable reproduction of experiments;
 - document all benchmark parameters;
 - provide a flexible execution model,
   with support for interrupting and continuing benchmarking;
 - enable the definition of complex sets of comparisons
   and their flexible execution;
 - report results to continuous performance monitoring systems,
   e.g., Codespeed or ReBenchDB;
 - provide basic support for building/compiling benchmarks/experiments
   on demand;
 - be extensible to parse output of custom benchmark harnesses.

ReBench isn't

 - a framework for microbenchmarks.
   Instead, it relies on existing harnesses and can be extended to parse their
   output.
 - a performance analysis tool. It is meant to execute experiments and
   record the corresponding measurements.
 - a data analysis tool. It provides only a bare minimum of statistics,
   but has an easily parseable data format that can be processed, e.g., with R.

To use ReBench, install it with Python's pip:

```bash
pip install rebench
```

### Acknowledgements

ReBench has been used by a number of people over the years, and their feedback
and [contributions](https://github.com/smarr/ReBench/graphs/contributors)
made it what it is today. Not all of these contributions are recorded,
but I'd still like to thank everyone, from the annoymous reviewer of artifacts,
to the students who had to wade through bugs and missing documentation.
Thank you!

### Changes Since 1.0rc2

 - moved CI to use GitHub Actions (#134)
 - added testing of Python 3.7 (#121) and ruamel.yaml (#123)
 - ensure config is YAML 1.2 compliant (#123)
 - added support for ReBenchDB (#129, #130)

 - fixed issues with error reporting (#128)
 - fixed handling of input size configuration (#117)

## [1.0rc2] - 2019-06-09

 - added `--setup-only` option, to run one benchmark for each setup (#110, #115)
 - added `ignore_timeout` setting to accept known timeouts without error (#118)
 - added `retries_after_failure` setting (#107, #108)

 - fixed data loading, which ignored warmup setting (#111, #116)
 - fixed how settings are inherited for follow documentation (#112, #113)
 - fixed message for consecutive failures (#109)
 - fixed some reporting issues (#106)

## [1.0rc1] - 2018-08-02

 - made user interface more consistent and concise (#83, #85, #92, #101, #102)
 - added concept of iterations/invocations (#82, #87)
 - added executor and suite name as command variables (#95, #101)
 - added and improved support for building suites before execution (#59, #78, #84, #96)
 - revised configuration format to me more consistent and add schema (#74, #82, #66, #94, #101)
 - fixed memory usage, avoid running out of memory for large experiments (#103)
 - added support to verify parameter and config file (#104)
 - added [documentation][docs] (#66, #101)
 - use PyLint (#79)

## [0.10.1] - 2018-06-08

 - fixed experiment filters and reporting on codespeed submission errors (#77)

## [0.10.0] - 2018-06-08

 - restructured command-line options in help, and use argparse (#73)
 - added support for Python 3 and PyPy (#65)
 - added support for extra criteria (things beside run time) (#64)
 - added support for path names in ReBenchLog benchmark names

## [0.9.1] - 2017-12-21

 - fixed time-left reporting of invalid times (#60)
 - take the number of data points per run into account for estimated time left (#62)
 - obtain process output on timeout to enable results of partial runs
 - fixed incompatibility with latest setuptools

## [0.9.0] - 2017-04-23

 - added support for building VMs before execution (#58)
 - added support for using binaries on system's path, `path` does not need
   to be provided for VM anymore (#57)

## [0.8.0] - 2016-06-25

 - added support for rerun experiments, see `-r` option (#50)
   This option will drop existing data for the selected experiment from
   the data file, and then execute them normally.
 - added support for filtering VM's and suites/benchmarks on CLI (#50)
 - directly output a programs stdout/stderr in verbose mode `-v` (#52)

 - fixed CLI reporting showing multiple summaries (#30)
 - fixed problem with quick termination (#51)

 - removed reporting to IRC, was never made to work properly
 - removed support for displaying confidence interval
   proper statistical evaluation needs to be done externally to ReBench
 - removed old support for Caliper output

## [0.7.5] - 2016-06-11

 - indicate failed runs as return code (#49)
 - added keep-alive message every 10min
 - changed debug output to show only last 20 data points
 - fixed `setup.py install`, remove non-existing package
 - started change log

## Untracked Releases
 - [0.7.4] - 2016-05-20
 - [0.7.3] - 2016-03-21
 - [0.7.2] - 2015-02-11
 - [0.7.1] - 2014-02-05
 - [0.6.0] - 2014-05-19
 - [0.5.0] - 2014-03-25

[Unreleased]: https://github.com/smarr/ReBench/compare/v1.3.0...HEAD
[1.3.0]:  https://github.com/smarr/ReBench/compare/v1.2.0...v1.3.0
[1.2.0]:  https://github.com/smarr/ReBench/compare/v1.1.0...v1.2.0
[1.1.0]:  https://github.com/smarr/ReBench/compare/v1.0.1...v1.1.0
[1.0.1]:  https://github.com/smarr/ReBench/compare/v1.0.0...v1.0.1
[1.0.0]:  https://github.com/smarr/ReBench/compare/v1.0rc2...v1.0.0
[1.0rc2]: https://github.com/smarr/ReBench/compare/v1.0rc1...v1.0rc2
[1.0rc1]: https://github.com/smarr/ReBench/compare/v0.10.1...v1.0rc1
[0.10.1]: https://github.com/smarr/ReBench/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/smarr/ReBench/compare/v0.9.1...v0.10.0
[0.9.1]: https://github.com/smarr/ReBench/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/smarr/ReBench/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/smarr/ReBench/compare/v0.7.5...v0.8.0
[0.7.5]: https://github.com/smarr/ReBench/compare/v0.7.4...v0.7.5
[0.7.4]: https://github.com/smarr/ReBench/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/smarr/ReBench/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/smarr/ReBench/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/smarr/ReBench/compare/v0.6.0...v0.7.1
[0.6.0]: https://github.com/smarr/ReBench/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/smarr/ReBench/compare/05dfc4b...v0.5.0
[docs]: http://rebench.readthedocs.io/
