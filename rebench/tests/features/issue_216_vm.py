#!/usr/bin/env python3
# simple script emulating an executor generating benchmark results
import sys

print(sys.argv)

print("Harness Name:", sys.argv[1])
print("Bench Name:", sys.argv[2])
print("Current Invocation:", sys.argv[3])

INVOCATION_NUM = int(sys.argv[3])
for i in range(0, INVOCATION_NUM):
    print("%d:RESULT-total:    %d.%d" % (i, i, i))
