import sys
import os

# Move the current working directory to that of the executable to ensure all assets are loaded correctly
if getattr(sys, "frozen", False):
	mvdir = sys.executable
else:
	mvdir = __file__

os.chdir(os.path.dirname(mvdir))
import gamesystem
