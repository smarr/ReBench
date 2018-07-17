# ReBench Configuration Format

The configuration format based on [YAML](http://yaml.org/)
and the most up-to-date documentation is generally the
[schema file](rebench-schema.yml).

# Basic Configuration

The main elements of each configuration are
[benchmarks suites](concepts.md#benchmark), [virtual machines (VMs)](concepts.md#vm),
and [experiments](concepts.md#experiment).

Below a very basic configuration file:

```YAML
# this run definition will be chosen if no parameters are given to rebench
default_experiment: all
default_data_file:  'example.data'

# a set of suites with different benchmarks and possibly different settings
benchmark_suites:
    ExampleSuite:
        gauge_adapter: RebenchLog
        command: Harness %(benchmark)s %(input)s
        input_sizes: [2, 10]
        benchmarks:
            - Bench1
            - Bench2

# a set of binaries use for the benchmark execution
virtual_machines:
    MyBin1:
        path: bin
        binary: test-vm2.py

# combining benchmark suites and benchmarks suites
experiments:
    Example:
        suites:
          - ExampleSuite
        executions:
          - MyBin1
```

This example shows the general structure of a ReBench configuration.

**General Settings.**
It can contain some general settings, for instance that all defined
experiments are going to be executed (as defined by the `default_experiment` key)
or that the data is to be stored in the `example.data` file.

**Benchmark Suites.** The `benchmark_suites` key is used to define collections of benchmarks.
A suite is defined by its name, here `ExampleSuite`, and by:

- a `gauge_adapter` to interpret the output of the suite's benchmark harness
- a `command` which is given to a virtual machine for execution
- possibly `input_sizes` to compare the behavior of benchmarks based on different parameters
- and a list of `benchmarks`

The `command` uses Python format strings to compose the command line string.
Since there are two benchmarks (`Bench1` and `Bench2`) and two input sizes (`2` and `10`),
this configuration defines four different [runs](concepts.md#run), for which
to record the data.

**Virtual Machines.** The `virtual_machines` key defines the VMs to use to
execute the runs defined by a benchmark suite. The `path` gives the relative
or absolute path where to find the `binary`.

**Experiments.** The `experiments` then combine suites and VMs to executions.
In this example it is simply naming the suite and the VM.

# Reference of the Configuration Format

As said before, configurations are [YAML](http://yaml.org/) files, which means
standard YAML features are supported. Furthermore, the format of configuration
files is defined as a [schema](rebench-schema.yml). The schema is used to
check the structure of a configuration for validity when it is loaded.  

In the reminder of this page, we detail all elements of the configuration file.

## Priority of Configuration Elements

Different configuration elements can define the same settings.
For instance a benchmark, a suite, and a VM can define a setting for
`input_sizes`. If this is the case, there is a priority for the different
elements and the one with the highest priority will be chosen.
Highest means here in terms of ranking, so the first in the list (benchmark),
overrides any other setting.

These priorities and the ability to define different benchmarks, suites, VMs, etc,
hopefully provides sufficient flexibility to encode all desired experiments.

The priorities are, starting with highest:

1. benchmark
2. benchmark suites
3. virtual machine
4. experiment
5. experiments
6. runs (as defined as the root element)

## Root Elements

**default_experiment:**

Defines the experiment to be run, if no other experiment is specified as a
command line parameter.
 
Default: `all`, i.e., all defined experiments are executed

Example:

```yaml
default_experiment: Example
```

---

**default_data_file:**

Defines the data file to be used, if nothing more specific is defined by an
experiment. The data format is CSV, the used separator is a tab (`\t`),
which allows to load the file for instance in Excel (though not recommended)
for a basic analysis.

Default: `rebench.data`

Example:

```yaml
default_data_file: my-experiment.data
```

---

**build_log:**

Defines the file to be used for logging the output of build operations.

Default: `build.log`

Example:

```yaml
build_log: my-experiment-build.log
```

---

**structured elements:**

In addition to the basic settings mentioned above, the following keys can
be used, and each contains structural elements further detailed below.

- `runs`
- `reporting`
- `benchmark_suites`
- `virtual_machines`
- `experiments`

---

**dot keys i.e. ignored configuration keys:**

To be able to use some YAML features, for instance [merge keys] or [node anchors],
it can be useful to define data that is not directly part of the configuration.
For this purpose, we allow dot keys on the root level that are ignored by the
schema check.

Example:
```YAML
.my-data: data  # excluded from schema validation
```

## Runs

The `runs` key defines global run details for all experiments.
All keys that can be used in the `runs` mapping can also be used for the
definition of a benchmark, benchmark suite, VM, a concrete experiment, and
the experiment in general.

**invocations:**

The number of times a virtual machine is executed a run.

Default: `1`

Example:

```yaml
runs:
  invocations: 100
```

---

**iterations:**

The number of times a run is executed within a virtual machine
invocation. This needs to be supported by a benchmark harness and
ReBench passes this value on to the harness or benchmark.

Default: `1`

Example:

```yaml
runs:
  iterations: 42
```

---

**warmup:**

Consider the first N iterations as warmup and ignore them in ReBench's summary
statistics. Note ,they are still persisted in the data file.

Default: `0`

Example:

```yaml
runs:
  warmup: 330
```

---

**min_iteration_time:**

Give a warning if the average total run time of an iteration is below this
value in milliseconds.

Default: `50`

Example:

```yaml
runs:
  min_iteration_time: 140
```

---

**max_invocation_time:**

Time in second after which an invocation is terminated.
The value -1 indicates that there is no timeout intended.

Default: `-1`

Example:

```yaml
runs:
  max_invocation_time: 600
```

---

**parallel_interference_factor:**

Setting used by parallel schedulers to determine the desirable degree of
parallelism. A higher factor means a lower degree of parallelism.

The problem with parallel executions is that they increase the noise observed
in the results.
![Use not recommended](https://img.shields.io/badge/Use%20Not%20Recommended-Jun%202018-orange.svg)

Example:

```yaml
runs:
  parallel_interference_factor: 10.5
```

---

**execute_exclusively:**

Determines whether the run is to be executed without any other runs being
executed in parallel.

The problem with parallel executions is that they increase the noise observed
in the results.
![Use not recommended](https://img.shields.io/badge/Use%20Not%20Recommended-Jun%202018-orange.svg)

Default: `true`

Example:

```yaml
runs:
  execute_exclusively: false
```

## Reporting

Currently, [Codespeed] is the only supported system for continuous
performance monitoring. It is configured with the `reporting` key. 

**codespeed:**

Send results to Codespeed for continuous performance tracking.
The settings define the project that is configured in Codespeed, and the
URL to which the results are reported. Codespeed requires more information,
but since these details depend on the environment, they are passed set on
the [command line](usage.md#continuous-performance-tracking). 

Example:

```yaml
reporting:
  codespeed:
    project: MyVM
    url:     http://example.org/result/add/json/
```

---

## Benchmark Suites

Benchmark suites are named collections of benchmarks and settings that apply to
all of them. 

**gauge_adapter:**

Name of the parser that interprets the output of the benchmark harness.
For a list of supported options see the list of [extensions](extensions.md#available-harness-support).

This key is mandatory.

Example:

```yaml
benchmark_suites:
  ExampleSuite:
    gauge_adapter: ReBenchLog
```

---

**command:**

The command for the benchmark harness. It's going to be combined with the
VM's command line. Thus, it should instruct the VM which harness to use
and how to map the various parameters to the corresponding harness settings.

It supports various format variables, including:
         
 - benchmark (the benchmark's name)
 - cores (the number of cores to be used by the benchmark)
 - input (the input variable's value)
 - iterations (the number of iterations)
 - suite (the name of the benchmark suite)
 - variable (another variable's value)
 - vm (the virtual machine's name)
 - warmup (the number of iterations to be considered warmup)

This key is mandatory.

Example:

```yaml
benchmark_suites:
  ExampleSuite:
    command: Harness %(benchmark)s --problem-size=%(input)s --iterations=%(iterations)s
```

---
        
**location:**

The path to the benchmark harness. Execution use this location as
working directory. It overrides the location/path of a VM.

Example:

```yaml
benchmark_suites:
  ExampleSuite:
    location: ../benchmarks/
```

---

**build:**

The given string is executed by the system's shell and can be used to
build a benchmark suite. It is executed once before any benchmarks of the suite
are executed. If `location` is set, it is used as working directory.
Otherwise, it is the current working directory of ReBench.

Example:

```yaml
benchmark_suites:
  ExampleSuite:
    build: ./build-suite.sh
```

---
      
**description/desc:**

The keys `description` and `desc` can be used to add a simple explanation of
the purpose of the suite.

Example:

```yaml
benchmark_suites:
  ExampleSuite:
    description: |
      This is an example suite for this documentation.
```

---

**benchmarks:**

The `benchmarks` key takes the list of benchmarks. Each benchmark is either a
simple name, or a name with additional properties.
See the section on [benchmark](#benchmark) for details.

Example:

```yaml
benchmark_suites:
  ExampleSuite:
    benchmark:
      - Benchmark1
      - Benchmark2:
          extra_args: "some additional arguments"
```

---

**run details and variables:**

A benchmark suite can additional use the keys for [run details](#runs) and
[variables](#benchmark).
Thus, one can use:

- `invocations`
- `iterations`
- `warmup`
- `min_iteration_time`
- `max_invocation_time`
- `parallel_interference_factor`
- `execute_exclusively`

As well as:

- input_sizes
- cores
- variable_values

Run configurations are generated from the cross product of all `input_sizes`,
`cores`, and `variable_values` for a benchmark.

## Benchmark

A benchmark can be define simply as a name. However, some times one might want
to define extra properties.

**extra_args:**

This extra argument is appended to the benchmark's command line.

Example:

```yaml
- Benchmark2:
    extra_args: "some additional arguments"
```

---

**command:**

ReBench will use this command instead of the name for the command line.

Example:

```yaml
- Benchmark2:
    command: some.package.Benchmark2
```

---

**codespeed_name:**

A name used for this benchmark when sending data to Codespeed.
This gives more flexibility to keep Codespeed and these configurations or
source code details decoupled.

Example:

```yaml
- Benchmark2:
    codespeed_name: "[peak] Benchmark2"
```

---

**input_sizes:**

Many benchmark harnesses and benchmarks take an input size as a
configuration parameter. It might identify a data file, or some other
way to adjust the amount of computation performed.

`input_sizes` expects a list, either as in the list notation below, or
in form of a sequence literal: `[small, large]`.

Run configurations are generated from the cross product of all `input_sizes`,
`cores`, and `variable_values` for a benchmark. 

Example:

```yaml
- Benchmark2:
    input_sizes:
      - small
      - large
```

---

**cores:**

The number of cores to be used by the benchmark.
At least that's the original motivation for the variable.
In practice, it is more flexible and just another variable that can take
any list of strings.

Run configurations are generated from the cross product of all `input_sizes`,
`cores`, and `variable_values` for a benchmark.

Example:

```yaml
- Benchmark2:
    cores: [1, 3, 4, 19]
```

---

**variable_values:**

Another dimension by which the benchmark execution can be varied.
It takes a list of strings, or arbitrary values really.

Run configurations are generated from the cross product of all `input_sizes`,
`cores`, and `variable_values` for a benchmark.

Example:

```yaml
- Benchmark2:
    variable_values:
      - Sequential
      - Parallel
      - Random
```

---

**run details:**

A benchmark suite can additional use the keys for [run details](#runs).

---

## Virtual Machines

The `virtual_machines` key defines the binaries and their settings to be used
to execute benchmarks. Each VM is a named set of properties.

**path:**

Path to the binary. If not given, it's up to the shell to find the binary.

Example:

```yaml
virtual_machines:
  MyBin1:
    path: .
```

---

**binary:**

The name of the binary to be used.

Example:

```yaml
virtual_machines:
  MyBin1:
    binary: my-vm
```

---

**args:**

The arguments given to the VM. They are given right after the binary.

Example:

```yaml
virtual_machines:
  MyBin1:
    args: --enable-assertions
```

---

**description and desc:**

The keys `description` and `desc` can be used to document the purpose of the
VM specified.

Example:

```yaml
virtual_machines:
  MyBin1:
    desc: A simple example for testing.
```

---

**build:**

The given string is executed by the system's shell and can be used to
build a VM. It is executed once before any benchmarks are executed with
the VM. If `path` is set, it is used as working directory. Otherwise,
it is the current working directory of ReBench.

Example:

```yaml
virtual_machines:
  MyBin1:
    build: |
      make clobber
      make
```

---

**run details and variables:**

A VM can additional use the keys for [run details](#runs) and [variables](#benchmark)
(`input_sizes`, `cores`, `variable_values`).

## Experiments

Experiments combine virtual machines and benchmark suites.
They can be defined by listing suites to be used and executions.
Executions can simply list VMs or also specify benchmark suites.
This gives a lot of flexibility to define the desired combinations.  

**description and desc:**

Description of the experiment with `description` or `desc`.

Example:

```yaml
experiments:
  Example:
    description: My example experiment.
```

---

**data_file:**

The data for this experiment goes into a separate file.
If not given, the `default_data_file` is used.

Example:

```yaml
experiments:
  Example:
    data_file: example.data
```

---

**reporting:**

Experiments can define specific reporting options.
See the [reporting](#reporting) for details on the properties.

Example:

```yaml
experiments:
  Example:
    reporting:
      codespeed:
        ...
```

---

**suites:**

List of benchmark suites to be used.

Example:

```yaml
experiments:
  Example:
    suites:
      - ExampleSuite
```

---

**executions:**

The VMs used for execution, possibly with specific suites assigned.
Thus `executions` takes a list of VM names, possibly with additional keys
to specify a suite and other details.

Example, simple list of VM names:

```yaml
experiments:
  Example:
    executions:
      - MyBin1
```

Example, execution with suite:

```yaml
experiments:
  Example:
    executions:
      - MyBin1:
          suites:
            - ExampleSuite
          cores: [3, 5]
```

---

**run details and variables:**

An experiment can additional use the keys for [run details](#runs) and
[variables](#benchmark) (`input_sizes`, `cores`, `variable_values`).
Note, this is possible on the main experiment, but also separately for each
of the defined executions.

[merge keys]: http://yaml.org/type/merge.html
[node anchors]: http://yaml.org/spec/1.1/current.html#id899912
[Codespeed]: https://github.com/tobami/codespeed/
