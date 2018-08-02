# Change Log

## [Unreleased]

 -

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

[Unreleased]: https://github.com/smarr/ReBench/compare/v1.0rc1...HEAD
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
