import requests
from flask import Blueprint, g, request, jsonify, abort
from db import get_db

api = Blueprint("api", __name__)

@api.route("/movies", methods=["GET"])
def api_movies_list():
    db = get_db()
    rows = db.execute("SELECT id, title, year, poster_url, is_watched, created_at FROM movies ORDER BY created_at DESC").fetchall()
    return jsonify([dict(row) for row in rows])

@api.route("/movies/<int:movie_id>", methods=["GET"])
def api_movies_get(movie_id):
    db = get_db()
    row = db.execute("SELECT id, title, year, poster_url, is_watched, created_at FROM movies WHERE id = ?", [movie_id]).fetchone()

    if row is None:
        abort(404, description="Movie not found")
    
    return jsonify(dict(row))

@api.route("/movies", methods=["POST"])
def api_movies_add():
    data = request.get_json(silent=True)

    if not data or "title" not in data:
        abort(400, description="Missing JSON or title")

    title = data["title"].strip()
    if len(title) < 2:
        abort(400, description="Title has to have at least 2 chars.")
        
    api_key = "ea92e9f7"
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    response = requests.get(url).json()

    if response.get("Response") == "False":
        abort(404, description="Movie not found in OMDb API")

    real_title = response.get("Title")
    year = response.get("Year")
    poster_url = response.get("Poster")

    db = get_db()
    existing_movie = db.execute("SELECT id FROM movies WHERE title LIKE ?", [real_title]).fetchone()
    if existing_movie:
        abort(400, description="This movie is already on the list.")

    is_watched = 1 if data.get("is_watched") else 0
    cur = db.execute("INSERT INTO movies(title, year, poster_url, is_watched) VALUES (?, ?, ?, ?)", [real_title, year, poster_url, is_watched])
    db.commit()

    movie_id = cur.lastrowid
    row = db.execute("SELECT id, title, year, poster_url, is_watched, created_at FROM movies WHERE id = ?", [movie_id]).fetchone()
    
    return jsonify(dict(row)), 201

@api.route("/movies/<int:movie_id>", methods=["PUT", "PATCH"])
def api_movies_update(movie_id):
    db = get_db()
    row = db.execute("SELECT id FROM movies WHERE id = ?", [movie_id]).fetchone()

    if row is None:
        abort(404, description="Movie not found")

    data = request.get_json(silent=True)

    if not data:
        abort(400, "Missing JSON")

    is_watched = data.get("is_watched")

    if is_watched is not None:
        db.execute("UPDATE movies SET is_watched = ? WHERE id = ?", [is_watched, movie_id])
    
    db.commit()

    updated_row = db.execute("SELECT id, title, year, poster_url, is_watched, created_at FROM movies WHERE id = ?", [movie_id]).fetchone()
    return jsonify(dict(updated_row))

@api.route("/movies/<int:movie_id>", methods=["DELETE"])
def api_movies_delete(movie_id):
    db = get_db()
    cur = db.execute("DELETE FROM movies WHERE id = ?", [movie_id])
    db.commit()

    if cur.rowcount == 0:
        abort(404, description="Movie not found")

    return "", 204