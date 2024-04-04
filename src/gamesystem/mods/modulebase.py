from pprint import pformat


class GameModule():
	ALIASES = []
	REQUIREMENTS = []

	def __init__(self, gameref):
		self.game = gameref

	def create(self):
		pass

	def __repr__(self):
		return type(self).__name__ + " " + pformat(self.__dict__)
