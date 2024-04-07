from prelude import *
from gamesystem import GameModule
from gamesystem.common.coroutines import TickCoroutine
from cards import PollutingCard, Card
from playspaces import Playspace



class InvestmentWatcher(Sprite):
	LAYER = "MANAGER"

	def update_move(self):
		tokens = 0
		while game.playerstate.funds >= 1.0:
			game.playerstate.funds -= 1.0
			tokens += 1

		for _ in range(tokens):
			game.sprites.new(Card.from_blueprint(game.blueprints.cards.investment))



@dataclass
class Scenario:
	name: str
	drawable_cards: List[str]
	starting_buildings: List[str]
	cards_per_turn: int

	@classmethod
	def from_blueprint(cls, j: Dict[str, Any]):
		return cls(**j)

	@classmethod
	def default(cls):
		return cls("default", [k for k, _ in game.blueprints.icards()], [k for k, _ in game.blueprints.ibuildings()], 6)


class PlayerTurnTakingModue(GameModule):
	IDMARKER = "playerturn"
	TURN_TRANSITION_LENGTH = 60

	REQUIREMENTS= ["blueprints"]

	def create(self):
		self.reset()
		self.scenario = Scenario.default()

	def reset(self):
		self.turn_count = 1
		self.transitioning = False

	def scene_start(self):
		game.sprites.new(InvestmentWatcher())

		for building in self.scenario.starting_buildings:
			game.sprites.new(Playspace.from_blueprint(game.blueprints.get_building(building)).with_tooltip())


	def next_turn(self):
		self.transitioning = False

		for _ in range(self.scenario.cards_per_turn):
			game.sprites.new(game.cardspawn.random())

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
			game.sprites.new(TickCoroutine(lifetime, lambda: game.playerstate.incr_property("pollution", consts.POLLUTION_UNPLAYED_INCR)), layer_override="MANAGER")
