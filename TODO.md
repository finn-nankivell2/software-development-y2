# TODO:

## Pictures TODO:

- [ ] - Cards:

	- [x] - Plastic

	- [x] - Compost

	- [x] - Aluminium

	- [x] - Metal

	- [x] - Unknown

	- [x] - Chemical

	- [x] - Paper

	- [x] - Investment


- [ ] - Building texture

	- [x] - Metal Recycling

	- [ ] - Electronic Recycling

	- [x] - Waste Sorting

	- [x] - Plastic recycling


## Sounds TODO:

- [ ] - Card play sounds

- [ ] - Polluting sounds

- [ ] - Investment sounds

- [ ] - UI clicking sounds

- [ ] - Music

	- [ ] - Internal playlist system?


## Game TODO:

- [x] - Mixed waste

	- Can be played to incenirator or landfill, but has a chance to cause a negative effect

	- Can be played to the sorter, which deals more sorted waste cards to you

- [x] - Make a prelude

- [x] - Card play effects

	- [x] - Become opaque and drift off

	- [x] - Trigger behaviour

- [x] - Card from json blueprint

- [x] - Building from json blueprint

- [x] - Draggable playspaces

- [x] - Playspace text and tooltip

- [x] - Palette module

- [ ] - Camera module

	- [x] - Just move the buildings left and right

	- [ ] - Mouse corner touch movement

	- [ ] - Move speed increase / easing

- [x] - Audio

- [x] - Text rendering

- [x] - UI Elements

- [x] - Investigate bug in asset loader where duplicate asset is loaded

	- So apparently it's because of how the TextureClippingCacheModule is handling the key creation for it's storage

	- You can have overlapping keys if the textures have the same size

- [x] - Set up proper logging

- [x] - Easing functions

- [x] - Turn taking system

	- [x] - End turn button

	- [x] - Cards fly off to pollution counter

	- [x] - New cards are dealt

	- [x] - Game state system of some kind

- [ ] - Buildings

	- [x] - Build new buildings

		- [x] - Investment special case

		- [x] - Wincondition building special case

		- [x] - Construction building special case

	- [x] - Building stamina system

		- [ ] - Update blueprints to use stamina, remove dataclass default

	- [x] - Upgrade system

		- [x] - Funds UI

		- [x] - Upgrade list

			- [x] - Tooltips

			- [x] - Upgrade Button class

			- [x] - Upgrade effects

				- [x] - Building transform effect

- [ ] - Balance stuff

	- [ ] - Difference between landfill and incineration?

	- [x] - Mixed waste sorting

	- [x] - Should capacity upgrades refund stamina?

		- Yes

	- [x] - Pollution chance to draw another card

- [ ] - Alternate background angles

- [x] - Fix massive bug with cards randomly disappearing from the game world

- [x] - Fix ghost tooltips and tooltips not being instantiated with cards

- [ ] - Main menu

	- [x] - Play: go to scenarios menu

	- [ ] - Tutorial

	- [x] - Exit

- [x] - Aspect preserving screen scaling

- [ ] - DOCUMENTATION

	- [ ] - Docstrings for reused classes

	- [ ] - Comment documentation

- [ ] - Scenarios menu

	- [ ] - Fancy scenario choice ui

	- [ ] - Highscores

- [ ] - Tutorial

- [x] - Flask server

- [ ] - Client side integration

- [x] - Fix pollution progress bar underflow

- [ ] - WIN STATE / LOSE STATE (important!!!!!)

	- [x] - Playspace movement locked

	- [x] - Card movement locked

		- [x] Remove update_move

	- [ ] - End of game stats

- [x] - Transitions

	- [x] - Completion hook

	- [x] - Reduction

- [ ] - Stylish player debug log ui

- [x] - Fix upgrade tooltips being misplaced

	- [x] - cached_rect fix
