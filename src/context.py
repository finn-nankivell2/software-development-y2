import sys
import os

if getattr(sys, "frozen", False):
	mvdir = sys.executable
else:
	mvdir = __file__

os.chdir(os.path.dirname(mvdir))
import gamesystem
