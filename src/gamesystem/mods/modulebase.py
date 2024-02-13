class GameModule():
	IDMARKER = "modulebase"
	ALIASES = []
	REQUIREMENTS = []

	def __init__(self, gameref):
		self.game = gameref

	def create(self):
		pass
