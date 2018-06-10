#!/usr/bin/env python
from __future__ import print_function

import sys

print(sys.argv)

print("Harness Name: ", sys.argv[1])
print("Bench Name:", sys.argv[2])
print("Input Size: ", sys.argv[3])

NAME = sys.argv[2]
print("RESULT-total: ", ("%s.%s" % (sys.argv[3], sys.argv[3])))

if NAME == "error-code":
    sys.exit(1)
elif NAME == "invalid":
    print("FAILED")

sys.exit(0)
