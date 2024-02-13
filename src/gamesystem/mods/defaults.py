from .modulebase import GameModule
from .baseclass import BaseSpriteManager, BaseLoopManager
from .sprites import SpritesManager

from collections import OrderedDict
from types import SimpleNamespace
import time


class StateManager(GameModule):
	IDMARKER = "state"

	def create(self):
		self.frames_since_start = 0

		self.deltatime = 0
		self.time_now = time.time()

	def update(self):
		self.frames_since_start += 1

		t = time.time()
		self.deltatime = t - self.time_now
		self.time_now = t


class GameloopManager(GameModule):
	IDMARKER = "loop"
	REQUIREMENTS = ["sprites"]

	def create(self, loop_hook=None):
		self.running = True
		self.game.loop = self
		self._hook = loop_hook

	def set_hook(self, new_hook):
		self._hook = new_hook

	def stop(self):
		self.running = False

	def do_running(self):
		if self._hook is None:
			self.game.sprites.update()
		else:
			self._hook(self)

	def run(self, loop):
		self.running = True
		loop()
		while self.running:
			self.do_running()


def default_modules():
	return [[SpritesManager, [["BG", "PLAYER", "FG"]]], [GameloopManager, []]]
