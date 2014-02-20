#!/usr/bin/env python
## simple script emulating a VM generating benchmark results
import sys
import random

print sys.argv

print "NumCores:", sys.argv[1]
print "BenchmarkHarness: ", sys.argv[2]
print "Benchmark: ", sys.argv[3]
print "InputSize: ", sys.argv[4]
print "FreeVar: ", sys.argv[5]

if sys.argv[1] == 4 or sys.argv[1] == 13:
    print "FAILED"
else:
    print "RESULT-part1: ", random.triangular(100, 110)
    print "RESULT-part2: ", random.triangular(400, 440)
    print "RESULT-part3: ", random.triangular(200, 300)
    print "RESULT-total: ", random.triangular(700, 850)