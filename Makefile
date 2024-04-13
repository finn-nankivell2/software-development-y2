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

dockerbuild:
	. venv/bin/activate
	mkdir build
	cp -r src/* build/
	cp requirements.txt build/program
	cd build/
	mv gamesystem program/gamesystem
	echo "import gamesystem" > program/context.py
	mv program src
	docker run -v $(shell pwd)/build/src:/usr/app/src kaspary/pyinstaller_build main.py
	cp src/build/dist/main.exe src
	cp src/build/dist/main src
	cd src
	mv main.exe program.exe
	mv main program

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
	yapf -r -i src/ tests/ -p

mypy:
	. venv/bin/activate
	dmypy start
	mypy src/program/ --pretty
	# mypy src/gamesystem/ --pretty

flake8:
	. venv/bin/activate
	flake8 src/program
