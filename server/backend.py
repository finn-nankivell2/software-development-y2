#!/usr/bin/env python3
from flask import Flask, request
import sqlite3
from dataclasses import dataclass

app = Flask(__name__)

# DATABASE STRUCTURE

# id, int, primary key
# username, string
# turn_count, int
# seconds, int
# pollution, int

@dataclass
class Entry:
	username: str
	turn_count: int
	seconds: int
	pollution: int

	@classmethod
	def from_data(cls, data):
		return cls(
			data["username"],
			int(data["turn_count"]),
			int(data["seconds"]),
			int(data["pollution"])
		)

	def generate_sql(self):
		return f"""
		INSERT INTO highscores (username, turn_count, seconds, pollution) VALUES (
			"{self.username}", {self.turn_count}, {self.seconds}, {self.pollution}
		);
		"""

def _verify_upload_data(data):
	def get_and_assert(key):
		d = data.get(key)
		assert d is not None, f"No value for {key}"
		return d

	username = get_and_assert("username")
	turn_count = get_and_assert("turn_count")
	seconds = get_and_assert("seconds")
	pollution = get_and_assert("pollution")

	assert len(username) <= 20, "Username length cannot be longer than 20"
	assert turn_count > 0, "turn_count must be a positive integer"
	assert seconds > 0, "seconds must be a positive integer"
	assert 0 <= pollution <= 100, "pollution must be an integer between 0 and 100"


@app.route("/upload", methods = ["POST"])
def upload():
	data = request.get_json(force=True)
	try:
		_verify_upload_data(data)
	except AssertionError as e:
		return str(e)

	entry = Entry.from_data(data)
	con = sqlite3.connect("highscores.db")
	cur = con.cursor()
	cur.execute(entry.generate_sql())
	con.commit()

	return "Submitted"


@app.route("/")
def index():
	return "Hello"


def startup():
	con = sqlite3.connect("highscores.db")
	creationq = """
	CREATE TABLE IF NOT EXISTS highscores(
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		username STRING NOT NULL,
		turn_count INTEGER NOT NULL,
		seconds INTEGER NOT NULL,
		pollution INTEGER NOT NULL
	)
	"""

	cur = con.cursor()


startup()
