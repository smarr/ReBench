#!/usr/bin/env python
# simple script emulating an executor generating benchmark results
from __future__ import print_function

import random
import os

print(os.environ)
if "IMPORTANT_ENV_VARIABLE" in os.environ:
    print("RESULT-total: ", random.triangular(700, 850))
