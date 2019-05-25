#!/usr/bin/env python
# simple script emulating an executor generating benchmark results
from __future__ import print_function

import sys
import random
from time import sleep

print(sys.argv)

print("Arg: ", sys.argv[1])
print("Harness Name: ", sys.argv[2])
print("Bench Name:", sys.argv[3])

for _ in range(10):
    print("RESULT-total: ", random.triangular(700, 850))

sys.stdout.flush()

sleep(10)
