#!/usr/bin/env python
# simple script emulating an executor generating benchmark results
from __future__ import print_function

import sys

print(sys.argv)

print("Harness Name: ", sys.argv[1])
print("Bench Name:", sys.argv[2])
print("Input Size: ", sys.argv[3])

INPUT_SIZE = int(sys.argv[3])

for i in range(0, INPUT_SIZE):
    print("%d:RESULT-bar:ms:   %d.%d" % (i, i, i))
    print("%d:RESULT-total:    %d.%d" % (i, i, i))
    print("%d:RESULT-baz:kbyte:   %d" % (i, i))
    print("%d:RESULT-foo:kerf: %d.%d" % (i, i, i))
