from prelude import *
from gamesystem import GameModule
from gamesystem.common.coroutines import TickCoroutine
from cards import PollutingCard, Card
from playspaces import Playspace
import fonts



class InvestmentWatcher(Sprite):
	LAYER = "MANAGER"

	def update_move(self):
		tokens = 0
		while game.playerstate.funds >= 1.0:
			game.playerstate.funds -= 1.0
			tokens += 1

		for _ in range(tokens):
			game.sprites.new(Card.from_blueprint(game.blueprints.cards.investment))



class PollutionWatcher(Sprite):
	LAYER = "MANAGER"

	def update_move(self):
		if game.playerstate.pollution >= 1.0:
			game.playerturn.game_over()



class GameComplete(Sprite):
	LAYER = "UI"

	def __init__(self, rect: FRect, victory: bool):
		self.surface = Surface(rect.size)
		self.surface.fill(palette.BLACK)
		self.surface.set_alpha(125)

		self.message = "You win!" if victory else "You lose!"
		self._font = fonts.families.roboto.size(70)
		self._render = self._font.render(self.message, True, palette.TEXT)

	def update_move(self):
		pass

	def update_draw(self):
		game.windowsystem.screen.blit(self.surface, VZERO)
		game.windowsystem.screen.blit(self._render, (game.windowsystem.dimensions - self._render.get_size()) / 2)


@dataclass
class Scenario:
	name: str
	drawable_cards: Dict[str, float]
	starting_buildings: List[str]
	buildable_buildings: List[str]
	cards_per_turn: int

	@classmethod
	def from_blueprint(cls, j: Dict[str, Any]):
		return cls(**j)

	@classmethod
	def default(cls):
		return cls(name="DEFAULT", drawable_cards={"investment": 0.5, "plastic": 0.5}, starting_buildings=["landfill", "incinerator"], buildable_buildings=["plasticrec"], cards_per_turn=4)

	def random_card_id(self, exclude: List[str] = []) -> str:
		roll = random.uniform(0, 1.0)
		start = 0

		highest_chance = None

		for play_id, chance in self.drawable_cards.items():
			if play_id in exclude:
				continue

			if start < roll <= start + chance:
				return play_id
			start += chance

			if chance == max(c for _, c in self.drawable_cards.items()):
				highest_chance = play_id

		if start != 1:
			logging.warn(f"Draw chances {start} do not add up to 1.0")

		return highest_chance

	def random_card(self, *args, **kwargs) -> Card:
		return game.cardspawn.get(self.random_card_id(*args, **kwargs)).with_tooltip()


class PlayerTurnTakingModue(GameModule):
	IDMARKER = "playerturn"
	TURN_TRANSITION_LENGTH = 60

	REQUIREMENTS= ["blueprints"]

	def create(self):
		self.reset()
		self.scenario = Scenario.default()

	def set_scenario_id(self, scenario_id):
		self.scenario = Scenario.from_blueprint(game.blueprints.get_scenario(scenario_id))
		self.reset()

	def _game_complete_init(self, victory: bool):
		if self.game_complete:
			return

		self.game_complete = True

		def empty(*args, **kwargs):
			pass

		for card in game.sprites.get("CARD"):
			card.destroy_anim()

		for space in game.sprites.get("PLAYSPACE"):
			space.update_move = empty

		for button in game.sprites.get("UI"):
			button.hovered = empty

		game.sprites.new(GameComplete(game.windowsystem.rect.copy(), victory))

	def you_win(self):
		self._game_complete_init(True)

	def game_over(self):
		self._game_complete_init(False)

	def reset(self):
		self.turn_count = 1
		self.transitioning = False
		self.game_complete = False

	def deal_card(self):
		game.sprites.new(self.scenario.random_card())

	def scene_start(self):
		game.sprites.new(InvestmentWatcher())
		game.sprites.new(PollutionWatcher())

		for building in self.scenario.starting_buildings:
			bp = game.blueprints.get_building(building)
			game.sprites.new(Playspace.from_blueprint(bp).with_tooltip())

	def next_turn(self):
		if self.game_complete:
			return

		self.transitioning = False

		for _ in range(self.scenario.cards_per_turn):
			game.sprites.new(self.scenario.random_card())

		for space in game.sprites.get("PLAYSPACE"):
			space.refill_stamina()

		chance = random.uniform(0, 1)
		if chance < game.playerstate.pollution:
			game.cardspawn.spawn("mixed")

		self.turn_count += 1

	def end_turn(self):
		if self.transitioning:
			return

		logging.info(f"Turn {self.turn_count} ended")

		self.transitioning = True

		timer = PlayerTurnTakingModue.TURN_TRANSITION_LENGTH if list(game.sprites.get("CARD")) else 10
		tick = TickCoroutine(timer, self.next_turn)
		game.sprites.new(tick, layer_override="MANAGER")

		cards = game.sprites.get("CARD")
		random.shuffle(cards)
		for i, card in enumerate(cards):
			lifetime = PlayerTurnTakingModue.TURN_TRANSITION_LENGTH - i*5

			if card.data.play_id != "investment":
				card.destroy_into_polluting(target=Vector2(game.spriteglobals.pollution_bar.rect.midtop), lifetime=lifetime)
				game.sprites.new(TickCoroutine(lifetime, lambda: game.playerstate.incr_property("pollution", consts.POLLUTION_UNPLAYED_INCR)), layer_override="MANAGER")
			else:
				card.destroy_anim()
