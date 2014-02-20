#!/usr/bin/env python
## simple script emulating a VM generating benchmark results
import sys
import random

print sys.argv

print "Harness Name: ", sys.argv[1]
print "Bench Name:",    sys.argv[2]
print "Input Size: ",   sys.argv[3]

input_size = int(sys.argv[3])

for i in range(0, input_size):
    print "RESULT-bar: ",   i
    print "RESULT-baz: ",   i
    print "RESULT-foo: ",   i
    print "RESULT-total: ", i
