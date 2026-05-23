from flask import Flask, g
import secrets
from db import get_db
from api.routes import api
from web.routes import web

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(web)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS movies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    year TEXT,
    poster_url TEXT,
    is_watched INTEGER NOT NULL DEFAULT 0 CHECK (is_watched IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_movies_is_watched ON movies(is_watched);
CREATE INDEX IF NOT EXISTS idx_movies_created_at ON movies(created_at);
"""

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()

@app.cli.command("init-db")
def init_db_command():
    init_db()
    print("✔ Zainicjowano bazę danych")

@app.cli.command("seed-db")
def seed_db_command():
    db = get_db()
    howManyMovies = db.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    if howManyMovies == 0:
        db.executemany("INSERT INTO movies(title, year, poster_url, is_watched) VALUES (?, ?, ?, ?)",
                       [
                           ["Incepcja", "2010", "https://link-do-plakatu.com/1.jpg", 1], 
                           ["Matrix", "1999", "https://link-do-plakatu.com/2.jpg", 0], 
                           ["Interstellar", "2014", "https://link-do-plakatu.com/3.jpg", 0]
                       ])
        db.commit()
        print("✔ Dane przykładowe zostały dodane do tabeli movies.")
    else:
        print("❌ Tabela movies zawiera już dane, seedowanie przerwane.")

if __name__ == "__main__":
    app.run(debug=True)