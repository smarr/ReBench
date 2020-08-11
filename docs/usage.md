# Usage

ReBench is a command-line tool. In the following, we will discuss its usage.
The complete set of options can be displayed with the `--help` argument:

```bash
$ rebench --help
Usage: rebench [options] <config> [exp_name] [e:$]* [s:$]*

Argument:
  config    required argument, file containing the experiment to be executed
  exp_name  optional argument, the name of an experiment definition
            from the config file
            If not provided, the configured default_experiment is used.
            If 'all' is given, all experiments will be executed.

  e:$       filter experiments to only include the named executor, example: e:EXEC1 e:EXEC3
  s:$       filter experiments to only include the named suite and possibly benchmark
              example: s:Suite1 s:Suite2:Bench3

...
```

[Configuration files](config.md) provide the setup for experiments by
defining benchmarks, benchmark suites, their parameters, and executors
to execute them.

### Basic Execution: Run Experiments

ReBench takes a given configuration file, executes the experiments and stores
the measurement results into the configured data file. Assuming a basic
configuration as seen in the [README](index.md#install), the following command
line will execute all experiments and store the results in the `example.data`
file:

```bash
$ rebench example.conf
```

This basic execution can be customized in various ways as explained below.

### Partial Execution: Run Some of the Experiments

Instead of executing the configured experiments, we can ask ReBench to only
execute a subset of them, a specific experiment, only selected executors, suites, and
benchmarks.

The [configuration file](config.md) allows us to select a
`default_experiment`. But we can override this setting with the `exp_name`
parameter. Thus, the following will execute only the `Example` experiment:

```bash
$ rebench example.conf Example
```

We can further restrict what is executed.
To only execute the `MyBin1` executor, we use:

```bash
$ rebench example.conf Example e:MyBin1
```

To further limit the execution, we can also select a specific benchmark from a
suite:

```bash
$ rebench example.conf Example e:MyBin1 s:ExampleSuite:Bench1
```

The filters are applied on the set of [runs](config.md#runs) identified by a configuration and
the chosen experiments. Thus, the above says to execute only `MyBin1`, and no
other executor. For the resulting runs, we also want to execute only
`Bench1` in the `ExampleSuite`. If we list additional executors, they are all
considered. Similarly, naming more benchmarks will include them all.

### Further Options

ReBench supports a range of other options to control execution.

#### Quick Runs, Iterations, Invocations, Building

The [configuration](config.md#invocation) uses the notion of iteration
and invocation to define how often an executor is started (invocation) and how many
times a benchmark is executed in the same executor execution (iteration).

We can override this setting with the following parameters:

```text
-in INVOCATIONS, --invocations INVOCATIONS
                 The number of times an executor is started to execute a run.
-it ITERATIONS, --iterations ITERATIONS
                 The number of times a benchmark is to be executed
                 within an executor execution.

-q, --quick      Execute quickly. Identical with --iterations=1 --invocations=1

--setup-only     Build all executors and suites, and run one benchmark for each executor.
                 This ensures executors and suites are built.
                 It Implies --iterations=1 --invocations=1.

-B, --without-building
                 Disables execution of build commands for executors and suites.
```

#### Discarding Data, Rerunning Experiments, and Faulty Runs

ReBench's normal execution mode will assume that it should accumulate all data
until a complete data set is reached.
This means, we can interrupt execution at any point and continue later and
ReBench will continue where it left off.

Some times, we may want to update some experiments and discard old data:

```text
-c, --clean   Discard old data from the data file (configured in the run description).
-r, --rerun   Rerun selected experiments, and discard old data from data file.
```

[Runs](concepts.md#run) may fail for a variety of reasons. A benchmark might be
buggy, the executor may be faulty or unavailable, or the run reaches the
[`max_invocation_time`](config.md#max_invocation_time).
To include all data generated for the benchmark until it failed,
we can use the `-f` option: 

```text
-f, --faulty  Include results of faulty or failing runs
```

#### Execution Order

We may care for a different order for the benchmark execution.
This could either be to get a quicker impression of the performance results,
or possibly to account for the complexity of benchmarking and ensure
that the order does not influence results. 

For this purpose we use *schedulers* to determine the execution order.

```text
-s SCHEDULER, --scheduler=SCHEDULER
                        execution order of benchmarks: batch, round-robin,
                        random [default: batch]
```

#### Prevent Execution to Verify Configuration

To check whether a configuration is correct, it can be useful to avoid
execution altogether. For such *testing* or *dry run*, we have the following
option:

```text
-E, --no-execution    Disables execution. It allows to verify the
                      configuration file and other parameters.
```  

#### Continuous Performance Tracking

ReBench supports [Codespeed][1] as platform for continuous performance
tracking. To report data to a Codespeed setup, the [configuration](config.md#codespeed)
needs to have the corresponding details.

And, Codespeed needs details on the concrete execution:

```text
--commit-id=COMMIT_ID     MANDATORY: when Codespeed reporting is  used, the
                          commit-id has to be specified.

--environment=ENVIRONMENT MANDATORY: name the machine on which the results are
                          obtained.

--branch=BRANCH           The branch for which the results have to be recorded,
                          i.e., to which the commit belongs. Default: HEAD

--executable=EXECUTABLE   The executable name given to Codespeed. Default: The
                          name used for the executor.

--project=PROJECT         The project name given to Codespeed. Default: Value
                          given in the config file.

-I, --disable-inc-report  Creates a final report at the end instead of reporting
                          incrementally.

-R, --disable-data-reporting Override the configuration and disable any reporting
                          to Codespeed and ReBenchDB.
```

[1]: https://github.com/tobami/codespeed/
