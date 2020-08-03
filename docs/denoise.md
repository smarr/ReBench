# Denoise

ReBench comes with the `rebench-denoise` tool, which adjusts system
settings to reduce the interference from the system that may influence
benchmark results.

`rebench-denoise` is a command-line tool, and supports the `--help` argument
for a brief overview of its options.

```bash
$ rebench-denoise --help 
usage: rebench-denoise [-h] [--version] [--json] [--without-nice] 
                       [--without-shielding]
                       command

positional arguments:
  command              `minimize`|`restore`|`exec -- `: `minimize` sets system
                       to reduce noise. `restore` sets system to the assumed
                       original settings. `exec -- ` executes the given
                       arguments.

optional arguments:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  --json               Output results as JSON for processing
  --without-nice       Don't try setting process niceness
  --without-shielding  Don't try shielding cores
```

ReBench will try to use `rebench-denoise` automatically.
However, it may be used as a stand-alone tool manually as well.

The commands are `minimize`, `restore`, and `exec`.

The `minimize` command will configure the system for reliable performance
and reduced interference.
The `restore` command will set the system back to a state that
is the presumed standard state.
With `exec`, the arguments provided after a `--` will be executed as a program.
Depending on the settings, this will include `nice -n-20` and the command to
use core shielding.
