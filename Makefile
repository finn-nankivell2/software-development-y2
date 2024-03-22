SHELL := /bin/bash
.ONESHELL:

env:
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

delenv:
	rm -r venv

dev:
	. venv/bin/activate
	python3 src/program/main.py

hackbuild:
	. venv/bin/activate
	mkdir build
	cp -r src/ build/
	cd build/src
	mv gamesystem hcktypr/gamesystem
	echo "import gamesystem" > hcktypr/context.py
	pyinstaller hcktypr/main.py --onefile --noconsole
	mv dist/main hcktypr/binary

release:
	. venv/bin/activate
	mkdir build
	cp -r src/ build/
	cd build/src
	mv gamesystem program/gamesystem
	echo "import gamesystem" > program/context.py
	pyinstaller hcktypr/main.py --onefile --noconsole
	mv dist/main program/binary

clean:
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

mypy:
	. venv/bin/activate
	mypy src/program/ --pretty

flake8:
	. venv/bin/activate
	flake8 src/program
