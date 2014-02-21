#!/usr/bin/env python
## simple script emulating a VM generating benchmark results
import sys

print sys.argv

print "Harness Name: ", sys.argv[1]
print "Bench Name:",    sys.argv[2]
print "Input Size: ",   sys.argv[3]

input_size = int(sys.argv[3])

for i in range(0, input_size):
    print "RESULT-bar:   %d.%d" % (i, i)
    print "RESULT-baz:   %d.%d" % (i, i)
    print "RESULT-foo:   %d.%d" % (i, i)
    print "RESULT-total: %d.%d" % (i, i)
