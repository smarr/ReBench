# Change Log

## [Unreleased]

 -

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

[Unreleased]: https://github.com/smarr/ReBench/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/smarr/ReBench/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/smarr/ReBench/compare/v0.7.5...v0.8.0
[0.7.5]: https://github.com/smarr/ReBench/compare/v0.7.4...v0.7.5
[0.7.4]: https://github.com/smarr/ReBench/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/smarr/ReBench/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/smarr/ReBench/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/smarr/ReBench/compare/v0.6.0...v0.7.1
[0.6.0]: https://github.com/smarr/ReBench/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/smarr/ReBench/compare/05dfc4b...v0.5.0
