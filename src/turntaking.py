from prelude import *
from gamesystem import GameModule
from gamesystem.common.coroutines import TickCoroutine
from cards import PollutingCard, Card
from playspaces import Playspace
import fonts
from gameutil import EasingVector2, BoxesTransition, ImageSprite, surface_rounded_corners
from ui import NamedButton
import requests


class InvestmentWatcher(Sprite):
	LAYER = "MANAGER"

	def update_move(self):
		tokens = 0
		while game.playerstate.funds >= 1.0:
			game.playerstate.funds -= 1.0
			tokens += 1

		for _ in range(tokens):
			game.sprites.new(Card.from_blueprint(game.blueprints.cards.investment).with_tooltip())



class PollutionWatcher(Sprite):
	LAYER = "MANAGER"

	def update_move(self):
		if game.playerstate.pollution >= 1.0:
			game.playerturn.game_over()



class GameComplete(Sprite):
	LAYER = "UI"
	ANIM_TIMING = 50

	def __init__(self, rect: FRect, victory: bool, disable_callback: Optional[Callable] = None):
		self.surface = Surface(rect.size)
		self.surface.fill(palette.BLACK)
		self.surface.set_alpha(GameComplete.ANIM_TIMING)

		self.message = "You win!" if victory else "You lose!"
		self._font = fonts.families.roboto.size(70)
		self._render = self._font.render(self.message, True, palette.TEXT)
		self._font_easing = EasingVector2(Vector2(game.windowsystem.dimensions.x/2, -200), Vector2(game.windowsystem.dimensions / 2), duration = GameComplete.ANIM_TIMING)
		self._font_pos = self._font_easing(0)

		self._frames = 0
		self._disable_callback = disable_callback
		self._add_buttons_lock = False

	def _alpha_halfway(self):
		return self._frames >= GameComplete.ANIM_TIMING

	def update_move(self):
		self._frames += 1
		if self._alpha_halfway():
			if self._frames < GameComplete.ANIM_TIMING*2:
				if self._disable_callback:
					self._disable_callback()
					self._disable_callback = None
				self._font_pos = self._font_easing(self._frames - GameComplete.ANIM_TIMING)
			elif not self._add_buttons_lock:
				def return_to_main_menu():
					game.sprites.new(BoxesTransition(game.windowsystem.rect.copy(), (16, 9), callback = lambda: game.loop.run(game.loop.functions.menu)))

				def submit_scores_to_server():
					submit_btn.disabled = True
					data = {
						"username": "default",
						"turn_count": game.playerturn.turn_count,
						"seconds": game.playerstate.time_since_game_start().total_seconds(),
						"pollution": int(game.playerstate.pollution * 100)
					}
					text = "Submitted"
					try:
						response = requests.post(consts.SERVER_ADDRESS + "/upload", json=data)
					except Exception as e:
						text = "Error!"
						logging.error(f"Request failed with {e} error")

					res_text = fonts.families.roboto.size(45).render(text, True, palette.TEXT)
					padding = Vector2(20, 20)
					bg = Surface(res_text.get_size() + padding)
					bg.fill(palette.BLACK)
					bg.blit(res_text, padding/2)

					game.sprites.new(ImageSprite(
						submit_btn.rect.midright + Vector2(40, 80),
						bg
					), layer_override="UI")

				buttons_start_at = self._font_pos.copy()
				buttons_size = Vector2(300, 120)
				game.sprites.new(NamedButton(
					FRect(buttons_start_at + Vector2(-(buttons_size.x + 30), 80), buttons_size),
					"MENU",
					onclick = return_to_main_menu
				))

				submit_btn = NamedButton(
					FRect(buttons_start_at + Vector2(30, 80), buttons_size),
					"SUBMIT STATS",
					onclick = submit_scores_to_server
				)

				game.sprites.new(submit_btn)
				self._add_buttons_lock = True

				stats_render = Surface((200, buttons_size.y))
				stats_render.fill(palette.BLACK)
				stats_render = surface_rounded_corners(stats_render, 5)

				# pygame.draw.rect(stats_render, palette.GREY, stats_render.get_rect().inflate(-10, -10), border_radius=5, width=2)

				stats = [
					f"Turns: {game.playerturn.turn_count}",
					f"Time: {game.playerstate.time_since_game_start()}",
					f"Pollution: {int(game.playerstate.pollution * 100)}%",
				]

				tpos = Vector2(20, 20)
				for text in stats:
					render = fonts.families.roboto.size(18).render(text, True, palette.TEXT)
					stats_render.blit(render, tpos)
					tpos.y += 30

				game.sprites.new(ImageSprite(submit_btn.rect.topright + Vector2(40, 0), stats_render), layer_override="UI")


	def update_draw(self):
		self.surface.set_alpha(min(self._frames, GameComplete.ANIM_TIMING)*4)
		game.windowsystem.screen.blit(self.surface, VZERO)
		if self._alpha_halfway():
			game.windowsystem.screen.blit(self._render, self._font_pos - Vector2(self._render.get_size())/2)


@dataclass
class Scenario:
	name: str
	scenario_id: str
	description: str
	drawable_cards: Dict[str, float]
	starting_buildings: List[str]
	buildable_buildings: List[str]
	cards_per_turn: int

	@classmethod
	def from_blueprint(cls, j: Dict[str, Any]):
		return cls(**j)

	@classmethod
	def default(cls):
		return cls(name="Default", scenario_id="default", description="Default Scenario", drawable_cards={"investment": 0.5, "plastic": 0.5}, starting_buildings=["landfill", "incinerator"], buildable_buildings=["plasticrec"], cards_per_turn=4)

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

	def _game_end_disable_elements(self):
		def empty(*args, **kwargs):
			pass

		for card in game.sprites.get("CARD"):
			card.destroy_anim()

		for space in game.sprites.get("PLAYSPACE"):
			space.update_move = empty

		for button in game.sprites.get("UI"):
			button.hovered = empty

	def _game_complete_init(self, victory: bool):
		if self.game_complete:
			return

		self.game_complete = True

		game.sprites.new(GameComplete(game.windowsystem.rect.copy(), victory, disable_callback=self._game_end_disable_elements))
		self._game_end_disable_elements()

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
