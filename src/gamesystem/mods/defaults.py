from .modulebase import GameModule
from .baseclass import BaseSpriteManager, BaseLoopManager
from .sprites import SpritesManager

from collections import OrderedDict
from types import SimpleNamespace
import time

import pygame


class StateManager(GameModule):
	IDMARKER = "state"

	class Timer:

		def __init__(self, length, state):
			self._length = length
			self._start = time.time()

			self._stateman = state

		def ratio(self):
			return self.elapsed() / self._length

		def elapsed(self):
			return self._stateman.time_now - self._start

		def complete(self):
			return self.elapsed() > self._length

	def create(self):
		self.frames_since_start = 0

		self.deltatime = 0
		self.time_now = time.time()

	def timer(self, length):
		return StateManager.Timer(length, self)

	def update(self):
		self.frames_since_start += 1

		t = time.time()
		self.deltatime = t - self.time_now
		self.time_now = t


class ClockManager(GameModule):
	IDMARKER = "clock"

	def create(self, framerate=60):
		self.framerate = framerate
		self.clock = pygame.time.Clock()

	def update(self):
		self.clock.tick(self.framerate)


class GameloopManager(GameModule):
	IDMARKER = "loop"
	REQUIREMENTS = ["sprites"]

	def create(self, loop_hook=None):
		self.running = False
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

	def run(self, inithook):
		if self.running:
			inithook()
			return

		self.running = True
		inithook()
		while self.running:
			self.do_running()


def default_modules():
	return [[SpritesManager, [["BG", "PLAYER", "FG"]]], [GameloopManager, []]]
