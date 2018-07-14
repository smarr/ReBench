# ReBench Configuration Format

The configuration format based on [YAML](http://yaml.org/)
and the most up-to-date documentation is generally the
[schema file](rebench-schema.yml).

## Basic Configuration

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

## Detailed Run Down

- basic correctness of the file is verified by validating it against the schema


 - runs
 - reporting
 - benchmark
 - variables
 - benchmark suites
 - virtual machine
 - experiment

 - custom data: any entry name starting with a dot:
   `.my-data: [2, 4]`

### Priority of Configuration Elements

- benchmark
- benchmark suites
- virtual machine
- experiment
- experiments
- runs


### Advanced Features

**dot keys i.e. ignored configuration keys:**

To be able to use some YAML features, for instance [merge keys] or [node anchors],
it can be useful to define data that is not directly part of the configuration.
For this purpose, we allow dot keys on the root level that are ignored by the
schema check.

Example:
```YAML
.my-data: data  # excluded from schema validation
```
 

[merge keys]: http://yaml.org/type/merge.html
[node anchors]: http://yaml.org/spec/1.1/current.html#id899912
