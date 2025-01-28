#!/usr/bin/env python3
import os
import sys

# get the environemnt variable LUA_PATH
lua_path = os.environ.get("LUA_PATH", "")
if lua_path == "?.lua;../../awfy/Lua/?.lua":
    print("Correct")
    sys.exit(0)
else:
    print("Error: LUA_PATH has unexpected value: " + lua_path)
    print("Previously we has stray single quotes around the value.")
    sys.exit(1)
