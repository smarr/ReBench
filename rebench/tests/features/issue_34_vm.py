#!/usr/bin/env python
import sys

print sys.argv

print "Harness Name: ", sys.argv[1]
print "Bench Name:",    sys.argv[2]
print "Input Size: ",   sys.argv[3]

name = sys.argv[2]
print "RESULT-total: ", ("%s.%s" % (sys.argv[3], sys.argv[3]))

if name == "error-code":
    sys.exit(1)
elif name == "invalid":
    print "FAILED"

sys.exit(0)
