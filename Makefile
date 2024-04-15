SHELL := /bin/bash
.ONESHELL:

env:
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

dev:
	. venv/bin/activate
	python3 src/main.py

release:
	. venv/bin/activate
	pyinstaller src/main.py --onedir --name bruascar
	cp -r src/assets/ src/data src/fonts src/sfx dist/bruascar

# dockerbuild:
# 	. venv/bin/activate
# 	mkdir build
# 	cp -r src/* build/
# 	cp requirements.txt build/program
# 	cd build/
# 	mv gamesystem program/gamesystem
# 	echo "import gamesystem" > program/context.py
# 	mv program src
# 	docker run -v $(shell pwd)/build/src:/usr/app/src kaspary/pyinstaller_build main.py
# 	cp src/build/dist/main.exe src
# 	cp src/build/dist/main src
# 	cd src
# 	mv main.exe program.exe
# 	mv main program

clean:
	rm -rf build dist

yapf:
	. venv/bin/activate
	yapf -r -i src/ tests/ -p

mypy:
	. venv/bin/activate
	dmypy start
	mypy src/ --pretty
	# mypy src/gamesystem/ --pretty

flake8:
	. venv/bin/activate
	flake8 src/
