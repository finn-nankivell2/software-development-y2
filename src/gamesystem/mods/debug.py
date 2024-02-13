from .modulebase import GameModule
import pygame.font
from pygame import Color


class DebugOverlayManager(GameModule):
	IDMARKER = "debug"
	REQUIREMENTS = ["windowsystem"]

	def create(
		self, fontsize: int = 30, font=None, fontcolour: Color = Color(255, 255, 255), fontaliasing: bool = False
	):
		pygame.font.init()
		self._fontsize = fontsize
		self._fontcolour = fontcolour
		self._fontaliasing = fontaliasing

		self._font = pygame.font.Font(font, self._fontsize) if type(font) is str or font is None else font
		self._queue = []

	def update(self):
		x = self._fontsize * 0.5
		for i, txt in enumerate(self._queue):
			y = (i + 0.5) * self._fontsize * 1.5
			rendered = self._font.render(txt, self._fontaliasing, self._fontcolour)
			self.game.windowsystem.uscreen.blit(rendered, (x, y))
		self._queue = []

	def output(self, txt):
		self._queue.append(str(txt))
