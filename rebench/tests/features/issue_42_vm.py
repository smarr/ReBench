#!/usr/bin/env python3
# simple script emulating an executor generating benchmark results
import random
import os
import sys

test = sys.argv[2]

env = os.environ.items()
env = sorted(env, key=lambda el: el[0])
print(test)
print(env)

known_envvars = ["PWD", "SHLVL", "VERSIONER_PYTHON_VERSION",
                 "_", "__CF_USER_TEXT_ENCODING", "LC_CTYPE",
                 "CPATH", "LIBRARY_PATH", "MANPATH", "SDKROOT"]

if test == "as-expected":
    if os.environ.get("IMPORTANT_ENV_VARIABLE", None) != "exists":
        sys.exit(1)

    if os.environ.get("ALSO_IMPORTANT", None) != "3":
        sys.exit(1)

    while env:
        e = env.pop()
        if (e[0] != "IMPORTANT_ENV_VARIABLE" and e[0] != "ALSO_IMPORTANT"
                and e[0] not in known_envvars):
            sys.exit(1)
elif test == "no-env":
    while env:
        e = env.pop()
        if e[0] not in known_envvars:
            print("Not in env: " + e[0])
            sys.exit(1)
elif test == "value-expansion":
    if os.environ.get("MY_VAR", None) is None:
        sys.exit(1)
    else:
        print("RESULT-total: ", os.environ.get("MY_VAR", None))
else:
    print("Unexpected test: " + test)
    sys.exit(1)

print("RESULT-total: ", random.triangular(700, 850))
