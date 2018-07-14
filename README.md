# ReBench: Execute and Document Benchmarks Reproducibly

[![Build Status](https://travis-ci.org/smarr/ReBench.svg?branch=master)](https://travis-ci.org/smarr/ReBench)
[![Documentation](https://readthedocs.org/projects/rebench/badge/?version=latest)](https://rebench.readthedocs.io/)
[![Codacy Quality](https://api.codacy.com/project/badge/Grade/2f7210b65b414100be03f64fe6702d66)](https://www.codacy.com/app/smarr/ReBench)

ReBench is a tool to run and document benchmark experiments.
Currently, it is mostly used for benchmarking language implementations,
but it can be used to monitor the performance of all
kind of other applications and programs, too.

The ReBench [configuration format][docs] is a text format based on [YAML](http://yaml.org/).
A configuration file defines how to build and execute a set of *experiments*,
i.e. benchmarks.
It describe which binary was used, which parameters where given
to the benchmarks, and the number of iterations to be used to obtain 
statistically reliable results.

With this approach, the configuration contains all benchmark-specific
information to reproduce a benchmark run. However, it does not capture
the whole system.

The data of all benchmark runs is recorded in a data file for later analysis.
Important for long-running experiments, benchmarks can be aborted and
continued at a later time.

ReBench is focuses on the execution aspect and does not provide advanced
analysis facilities itself. Instead, it is used in combination with
for instance R scripts to process the results or [Codespeed][1] to do continuous
performance tracing.

The documentation is hosted at [http://rebench.readthedocs.io/][docs].

## Goals and Features

ReBench is designed to

 - enable reproduction of experiments
 - document all benchmark parameters
 - a flexible execution model,
   with support for interrupting and continuing benchmarking
 - defining complex sets of comparisons and executing them flexibly
 - report results to continuous performance monitoring systems, e.g., [Codespeed][1]
 - basic support to build/compile benchmarks/experiments on demand
 - extensible support to read output of benchmark harnesses

## Non-Goals

ReBench isn't

 - a framework for microbenchmark.
   Instead, it relies on existing harnesses and can be extended to parse their
   output.
 - a performance analysis tool. It is meant to execute experiments and
   record the corresponding measurements.
 - a data analysis tool. It provides only a bare minimum of statistics,
   but has an easily readable data format that can be processed, e.g., with R.

## Installation and Usage

<a id="install"></a>

ReBench is implemented in Python and can be installed via pip:

```bash
pip install rebench
```

A minimal configuration file looks like:

```yaml
# this run definition will be chosen if no parameters are given to rebench
default_experiment: all
default_data_file:  'example.data'

# a set of suites with different benchmarks and possibly different settings
benchmark_suites:
    ExampleSuite:
        gauge_adapter: RebenchLog
        command: Harness %(benchmark)s %(input)s %(variable)s
        input_sizes: [2, 10]
        variable_values:
            - val1
        benchmarks:
            - Bench1
            - Bench2

# a set of binaries use for the benchmark execution
virtual_machines:
    MyBin1:
        path: bin
        binary: test-vm1.py %(cores)s
        cores: [1]
    MyBin2:
        path: bin
        binary: test-vm2.py

# combining benchmark suites and benchmarks suites
experiments:
    Example:
        suites:
          - ExampleSuite
        executions:
            - MyBin1
            - MyBin2
```

Saved as `test.conf`, it could be executed with ReBench as follows:

```bash
rebench test.conf
```

See the documentation for details: [http://rebench.readthedocs.io/][docs].

## Support and Contributions

In case you encounter issues,
please feel free to [open an issue](https://github.com/smarr/rebench/issues/new)
so that we can help.

For contributions, we use the [normal Github flow](https://guides.github.com/introduction/flow/)
of pull requests, discussion, and revisions. For larger contributions,
it is likely useful to discuss them upfront in an issue first.


[1]: https://github.com/tobami/codespeed/
[docs]: http://rebench.readthedocs.io/
