#!/usr/bin/env python
# simple script emulating a VM generating benchmark results
from __future__ import print_function
import sys
import random

print("test-vm2.py: args=" + str(sys.argv))

print("RESULT-part1: " + str(random.uniform(100, 110)))
print("RESULT-part2: " + str(random.uniform(400, 440)))
print("RESULT-part3: " + str(random.uniform(200, 300)))
print("RESULT-total: " + str(random.uniform(700, 850)))
