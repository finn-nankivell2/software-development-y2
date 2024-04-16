from prelude import *


class Particle(Sprite):
	LAYER = "PARTICLE"

	def __init__(self, pos, size, vel, colour, lifetime=60):
		self.pos = pos
		self.size = size
		self.vel = vel
		self.colour = colour
		self.outline = self.colour.lerp(Color("#ffffff"), 0.5)
		self._decay = self.size / lifetime

	@classmethod
	def rand_angle(cls, *args, speed=5, **kwargs):
		a = random.randint(0, 359)
		kwargs["vel"] = Vector2(math.cos(a), math.sin(a)) * speed
		return cls(*args, **kwargs)

	def update_move(self):
		self.pos += self.vel
		self.size -= self._decay
		if self.size < 1:
			self.destroy()

	def update_draw(self):
		pygame.draw.circle(game.windowsystem.screen, self.colour, self.pos, self.size)


class SurfaceParticle(Particle):

	def __init__(self, pos, vel, surface, lifetime=60):
		super().__init__(pos, surface.get_width() / 2, vel, Color("#ff00ff"), lifetime)
		self.surface = surface
		self._start_size = Vector2(self.surface.get_size())

	def update_draw(self):
		scale_to = Vector2(self.size, self.size) * 2
		self.surface = pygame.transform.scale(self.surface, scale_to)

		game.windowsystem.screen.blit(self.surface, self.pos - Vector2(self.surface.get_size()) / 2)


class DeflatingParticle(Particle):
	def __init__(self, rect, colour, lifetime=60):
		super().__init__(Vector2(rect.topleft), rect.width, VZERO, colour, lifetime)
		self.rect = rect
		self._deflate = -self.rect.height / lifetime

	def update_move(self):
		self.rect.inflate_ip(self._deflate, self._deflate)
		if self.rect.height < 1 or self.rect.width < 1:
			self.destroy()

	def update_draw(self):
		pygame.draw.rect(game.windowsystem.screen, self.colour, self.rect, border_radius=5)




def particle_explosion(number, *args, particle_type=Particle, **kwargs) -> List[Particle]:
	parts = []
	for _ in range(number):
		if kwargs.get("speed"):
			kwargs["speed"] *= random.uniform(0.6, 1.4)
		else:
			kwargs["speed"] = random.randint(3, 10)

		if kwargs.get("lifetime"):
			kwargs["lifetime"] *= random.uniform(0.6, 1.4)
		else:
			kwargs["lifetime"] = random.randint(40, 70)

		parts.append(particle_type.rand_angle(*args, **kwargs))

	return parts


class BubbleParticleEmitter(SpriteGroup):
	LAYER = "BACKGROUND"

	def __init__(self, pos=Vector2(0, 0), colours=["#923efc", "#6e1698"], mouse_follow=False):
		super().__init__()

		self.pos = pos
		colours = list(map(Color, colours))
		self.c1, self.c2 = colours
		self.mouse_follow = mouse_follow

	def update_move(self):
		a = random.randint(0, 180)
		vel = Vector2(math.cos(a), math.sin(a))

		c = self.c1.lerp(self.c2, random.uniform(0.0, 1.0))
		part = Particle(
			Vector2(self.pos),
			95,
			vel,
			c,
			lifetime=1120 + random.randint(-50, 50),
		)

		if self.mouse_follow:
			self.pos = game.input.mouse_pos()
			if game.input.mouse_down(0):
				self.sprites.append(part)
		else:
			self.sprites.append(part)

		super().update_move()

	def update_draw(self):
		for part in reversed(self.sprites):
			pygame.draw.circle(game.windowsystem.screen, part.outline, part.pos, part.size + 6)

		for part in reversed(self.sprites):
			pygame.draw.circle(game.windowsystem.screen, part.colour, part.pos, part.size)
