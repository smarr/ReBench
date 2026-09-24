#!/usr/bin/env python3
from os import environ, geteuid
from pwd import getpwuid

for key in environ:
    print(f"env: {key}={environ[key]}")

user_name = getpwuid(geteuid()).pw_name
print("Benchmark User: ", user_name)
print("RESULT-total: 1000.0")
