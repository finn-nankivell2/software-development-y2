SHELL := /bin/bash
.ONESHELL:

env:
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

clean:
	rm -r venv

dev:
	source venv/bin/activate
	python3 tests/gametest.py

test:
	. venv/bin/activate
	pytest tests/tests.py -v

yapf:
	. venv/bin/activate
	yapf -r -i src/ tests/ --style style.toml -p
