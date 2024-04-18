# TODO:

## Pictures TODO:

- [ ] - Cards:

	- [ ] - Plastic

	- [x] - Compost

	- [ ] - Aluminium

	- [ ] - Metal

	- [ ] - Misc Waste

	- [ ] - Chemical

	- [x] - Paper


- [ ] - Building texture

	- [x] - Metal Recycling

	- [ ] - Electronic Recycling

	- [x] - Waste Sorting


## Sounds TODO:

- [ ] - Card play sounds

- [ ] - Polluting sounds

- [ ] - Investment sounds

- [ ] - UI clicking sounds

- [ ] - Music


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

	- [ ] - Upgrade system

		- [x] - Funds UI

		- [x] - Upgrade list

			- [x] - Tooltips

			- [x] - Upgrade Button class

			- [ ] - Upgrade effects

				- [ ] - Building transform effect

- [ ] - Balance stuff

	- [ ] - Difference between landfill and incineration?

	- [x] - Mixed waste sorting

	- [ ] - Should capacity upgrades refund stamina?

- [ ] - Alternate background angles

- [x] - Fix massive bug with cards randomly disappearing from the game world

- [x] - Fix ghost tooltips and tooltips not being instantiated with cards

- [ ] - Refactor layer system to use enum

- [ ] - Main menu

- [x] - Aspect preserving screen scaling

- [ ] - DOCUMENTATION

	- [ ] - Docstrings for reused classes

	- [ ] - Comment documentation

- [ ] - Scenarios menu

- [ ] - Tutorial

- [ ] - Flask server

- [ ] - Fix pollution progress bar underflow

- [ ] - WIN STATE / LOSE STATE (important!!!!!)

	- [ ] - Playspace movement locked?

	- [ ] - Card movement locked?

		- Remove update_move?
