import pygame.surfarray
from pygame import Surface

import numpy as np
from perlin_numpy import generate_perlin_noise_2d, generate_fractal_noise_2d, generate_perlin_noise_3d, generate_fractal_noise_3d


def perlin_surface(dims, seed: float) -> Surface:
	pass


DIMS = (1280, 720)
window = pygame.display.set_mode(DIMS)

surf = perlin_surface(DIMS, 1.0)

# window.blit(surf, (0, 0))

while True:
	pygame.display.flip()
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			exit()
