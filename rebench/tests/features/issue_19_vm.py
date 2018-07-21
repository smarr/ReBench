#!/usr/bin/env python
# simple script emulating an executor generating benchmark results
from __future__ import print_function

import sys
import random

print(sys.argv)

print("Harness Name: ", sys.argv[1])
print("Bench Name:", sys.argv[2])
print("Input Size: ", sys.argv[3])

print("RESULT-total: ", random.triangular(700, 850))
