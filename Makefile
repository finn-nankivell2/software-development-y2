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
	pyinstaller bruascar.spec --noconfirm
	cp -r src/assets/ src/data src/fonts src/sfx dist/bruascar

run:
	./dist/bruascar/bruascar

dockerbuild:
	. venv/bin/activate
	docker run -v $(shell pwd):/usr/app/src kaspary/pyinstaller_build src/main.py

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
