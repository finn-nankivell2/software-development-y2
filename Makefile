SHELL := /bin/bash
.ONESHELL:

env:
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

dev:
	. venv/bin/activate
	python3 src/main.py

backend:
	. venv/bin/activate
	cd server
	flask --app hello run

release:
	. venv/bin/activate
	pyinstaller theworks.spec --noconfirm
	cp -r src/assets/ src/data src/fonts src/sfx dist/TheWorks

run:
	./dist/TheWorks/TheWorks

# dockerbuild:
# 	. venv/bin/activate
# 	docker run -v $(shell pwd):/usr/app/src kaspary/pyinstaller_build src/main.py

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
