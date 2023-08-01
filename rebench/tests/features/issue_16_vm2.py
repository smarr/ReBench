#!/usr/bin/env python3
# simple script emulating an executor generating benchmark results
import sys

print(sys.argv)

print("Harness Name: ", sys.argv[1])
print("Bench Name:", sys.argv[2])
print("Input Size: ", sys.argv[3])

INPUT_SIZE = int(sys.argv[3])

for i in range(0, INPUT_SIZE):
    if i % 2 == 0:
        print("RESULT-bar:   %d.%d" % (i, i))
    if i % 3 == 0:
        print("RESULT-baz:   %d.%d" % (i, i))
    if i % 2 == 1:
        print("RESULT-foo:   %d.%d" % (i, i))

    print("RESULT-total: %d.%d" % (i, i))
