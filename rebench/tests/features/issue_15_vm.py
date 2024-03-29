#!/usr/bin/env python3
# simple script emulating an executor generating benchmark results
import sys
import random

print(sys.argv)

print("Harness Name: ", sys.argv[1])
print("Bench Name:", sys.argv[2])
print("Warmup: ", sys.argv[3])

WARMUP = int(sys.argv[3])

for i in range(0, WARMUP):
    print("RESULT-total: ", random.triangular(700, 850) * 2)

print("RESULT-total: ", random.triangular(700, 850))
