# ReBench: Execute and Document Benchmarks Reproducibly

[![Build Status](https://travis-ci.org/smarr/ReBench.svg?branch=master)](https://travis-ci.org/smarr/ReBench)
[![Documentation](https://readthedocs.org/projects/rebench/badge/?version=latest)](https://rebench.readthedocs.io/)
[![Codacy Quality](https://api.codacy.com/project/badge/Grade/2f7210b65b414100be03f64fe6702d66)](https://www.codacy.com/app/smarr/ReBench)

ReBench is a tool to run and document benchmark experiments.
Currently, it is mostly used for benchmarking language implementations,
but it can be used to monitor the performance of all
kind of other applications and programs, too.

The ReBench configuration format is a text format based on [YAML](http://yaml.org/).
A configuration file defines how to build and execute a set of *experiments*,
i.e. benchmarks.
It describe which binary was used, which parameters where given
to the benchmarks, and the number of iterations to be used to obtain 
statistically reliable results.

With this approach, the configuration contains all benchmark-specific
information to reproduce a benchmark run. However, it does not capture
the whole system.

The data of all benchmark runs is recorded in a data file and allows to 
continue aborted benchmark runs at a later time.

ReBench is designed to focus on the execution and does not provide advanced
analysis facilities itself. Instead, it is typically used in combination with
for instance R scripts to process the results or [Codespeed][1] to do continuous
performance tracing.

## Features

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

ReBench is not a

 - framework for microbenchmark, or benchmarks in general.
   Instead, it relies on existing harnesses and can be extended to parse their
   output.
 - a performance analysis tool. It is only meant to execute experiments and
   record the corresponding measurements. 

## Usage

ReBench is implemented in Python and can be installed via pip:

```bash
pip install rebench
```

A minimal configuration file looks like:

```yaml
# this run definition will be chosen if no parameters are given to rebench
standard_experiment: Test
standard_data_file:  'tests/small.data'

# general configuration for runs
runs:
    number_of_data_points:  10

# a set of suites with different benchmarks and possibly different settings
benchmark_suites:
    Suite:
        gauge_adapter: TestVM
        command: TestBenchMarks %(benchmark)s %(input)s %(variable)s
        input_sizes: [2, 10]
        variable_values: val1
        benchmarks:
            - Bench1
            - Bench2

# a set of binaries use for the benchmark execution
virtual_machines:
    TestRunner1:
        path: tests
        binary: test-vm1.py %(cores)s
        cores: [1]
    TestRunner2:
        path: tests
        binary: test-vm2.py

# combining benchmark suites and benchmarks suites
experiments:
    Test:
        benchmark: Suite
        executions:
            - TestRunner1
            - TestRunner2
```

Saved as `test.conf`, it could be executed with ReBench as follows:

```bash
rebench test.conf
```

## Support and Contributions

In case you encounter issues,
please feel free to [open an issue](https://github.com/smarr/rebench/issues/new)
so that we can help.

For contributions, we use the [normal Github flow](https://guides.github.com/introduction/flow/)
of pull requests, discussion, and revisions. For larger contributions,
it is likely useful to discuss them upfront in an issue first.


[1]: https://github.com/tobami/codespeed/
