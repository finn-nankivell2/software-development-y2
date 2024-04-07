from prelude import *
from gamesystem import GameModule
from gamesystem.common.coroutines import TickCoroutine
from cards import PollutingCard, Card


class PlayerTurnTakingModue(GameModule):
	IDMARKER = "playerturn"
	TURN_TRANSITION_LENGTH = 60

	def create(self):
		self.reset()

	def reset(self):
		self.turn_count = 1
		self.transitioning = False

	def scene_start(self):
		# add sprites here
		pass

	def next_turn(self):
		self.transitioning = False

		for _ in range(3):
			bprint = random.choice([v for _, v in game.blueprints.icards()])
			game.sprites.new(Card.from_blueprint(bprint).with_tooltip())

		self.turn_count += 1

	# TODO: Random polluting card lifetimes

	def end_turn(self):
		if self.transitioning:
			return

		logging.info(f"Turn {self.turn_count} ended")

		self.transitioning = True

		timer = PlayerTurnTakingModue.TURN_TRANSITION_LENGTH if list(game.sprites.get("CARD")) else 10
		tick = TickCoroutine(timer, self.next_turn)
		game.sprites.new(tick, layer_override="MANAGER")

		for i, card in enumerate(game.sprites.get("CARD")):
			lifetime = lifetime=PlayerTurnTakingModue.TURN_TRANSITION_LENGTH - i*5
			card.destroy_into_polluting(target=Vector2(game.spriteglobals.pollution_bar.rect.midtop), lifetime=lifetime)
			game.sprites.new(TickCoroutine(lifetime, lambda: game.playerstate.incr_property("pollution", 0.1)), layer_override="MANAGER")
