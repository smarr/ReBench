#!/usr/bin/env python
# simple script emulating a VM generating benchmark results
import sys
import random
from __future__ import print_function

print("test-vm2.py: args=", sys.argv)

print("RESULT-part1: ", random.uniform(100, 110))
print("RESULT-part2: ", random.uniform(400, 440))
print("RESULT-part3: ", random.uniform(200, 300))
print("RESULT-total: ", random.uniform(700, 850))
