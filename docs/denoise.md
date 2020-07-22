# Denoise

ReBench comes with the `rebench-denoise` tool, which adjusts system
settings to reduce the interference from the system that may influence
benchmark results.

`rebench-denoise` is a command-line tool, and supports the `--help` argument
for a brief overview of its options.

```bash
$ rebench-denoise --help 
usage: rebench-denoise [-h] [--version] [--json] command

positional arguments:
  command     Either set system to 'minimize' noise or 'restore' the settings
              assumed to be the original ones

optional arguments:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
  --json      Output results as JSON for processing
```

ReBench will try to use `rebench-denoise` automatically.
However, it may be used as a stand-alone tool manually as well.

The two key commands are `minimize` and `restore`.

The `minimize` command will configure the system for reliable performance
and reduced interference.
The `restore` command will set the system back to a state that
is the presumed standard state.
