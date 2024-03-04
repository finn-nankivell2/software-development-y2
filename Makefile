SHELL := /bin/bash
.ONESHELL:

env:
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

cleanenv:
	rm -r venv

dev:
	. venv/bin/activate
	python3 src/program/main.py

build:
	. venv/bin/activate
	mkdir build
	cp -r src/ build/
	cd build/src
	mv gamesystem hcktypr/gamesystem
	# python3 hcktypr/main.py
	pyinstaller hcktypr/main.py --onefile --noconsole
	mv dist/main hcktypr/binary

cleanbuild:
	rm -r build

hacktyper:
	. venv/bin/activate
	python3 src/hcktypr/main.py

test:
	. venv/bin/activate
	pytest tests/tests.py -v

yapf:
	. venv/bin/activate
	yapf -r -i src/ tests/ --style style.toml -p
