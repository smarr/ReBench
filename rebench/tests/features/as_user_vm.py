#!/usr/bin/env python3
# simple script emulating an executor generating benchmark results
from getpass import getuser
from os import environ

for key in environ:
    print(f"env: {key}={environ[key]}")

print("Benchmark User: ", getuser())
print("RESULT-total: 1000.0")
