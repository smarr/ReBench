#!/usr/bin/env python
# simple script emulating an executor generating benchmark results
from __future__ import print_function

import random
import os

if ("IMPORTANT_ENV_VARIABLE" not in os.environ) or (os.environ["IMPORTANT_ENV_VARIABLE"] != "iexist"):
    exit()

if ("ALSOIMPORTANT" not in os.environ) or (os.environ["ALSOIMPORTANT"] != "3"):
    exit()

# If it prints, the test is considered to have succeeded
print("RESULT-total: ", random.triangular(700, 850))
