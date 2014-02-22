#!/usr/bin/env python
## simple script emulating a VM generating benchmark results
import sys
import random

print sys.argv

print "Harness Name: ", sys.argv[1]
print "Bench Name:",    sys.argv[2]
print "Input Size: ",   sys.argv[3]

print "RESULT-total: ", random.triangular(700, 850)
