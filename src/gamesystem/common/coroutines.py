from .sprite import Sprite


class TickCoroutine(Sprite):

	def __init__(self, ticks, callback):
		self._ticks = ticks
		self._ticker = 0
		self._callback = callback

	def update_move(self):
		self._ticker += 1
		if self._ticker >= self._ticks:
			self.destroy()
			self._callback()
