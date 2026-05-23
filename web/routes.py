import requests
from flask import Blueprint, render_template, g, redirect, url_for, flash, request
from db import get_db

web = Blueprint("web", __name__)

@web.route("/")
def index():
    return render_template("index.html")

@web.route("/ping-db")
def ping_db():
    db = get_db()
    db.execute("SELECT 1").fetchone()
    return render_template("ping.html")

@web.route("/list_movies")
def list_movies():
    db = get_db()
    movies = db.execute("SELECT id, title, year, poster_url, is_watched, created_at FROM movies ORDER BY created_at DESC").fetchall()
    return render_template("list_movies.html", movies=movies)

@web.route("/movie/<int:movie_id>")
def movie(movie_id):
    db = get_db()
    movie_data = db.execute("SELECT id, title, year, poster_url, is_watched, created_at FROM movies WHERE id = ?", [movie_id]).fetchone()
    if movie_data is None:
        flash("Nie znaleziono takiego filmu w bazie danych.")
        return redirect(url_for("web.list_movies"))
    return render_template("movie_details.html", movie=movie_data)

@web.route("/add_movie",  methods=["GET", "POST"])
def add_movie():
    if request.method == "POST":
        title = request.form.get("title")
        if not title or len(title.strip()) < 2:
            flash("Tytuł filmu musi mieć przynajmniej 2 znaki.")
            return render_template("add_movie.html", title=title)
        
        api_key = "ea92e9f7"
        url = "https://www.omdbapi.com/"
        
        params = {
            "t": title,
            "apikey": api_key
        }
        
        response = requests.get(url, params=params).json()

        if response.get("Response") == "False":
            error_english = response.get("Error", "Nieznany błąd")
            
            translations = {
                "Movie not found!": "Nie znaleziono filmu!",
                "Invalid API key!": "Nieprawidłowy klucz API!",
                "Too many results.": "Zbyt wiele wyników. Podaj dokładniejszy tytuł."
            }
            
            error_polish = translations.get(error_english, error_english)
            
            flash(f"Błąd API: {error_polish}")
            return render_template("add_movie.html", title=title)

        real_title = response.get("Title")
        year = response.get("Year")
        poster_url = response.get("Poster")

        db = get_db()
        existing_movie = db.execute("SELECT id FROM movies WHERE title LIKE ?", [real_title]).fetchone()
        if existing_movie:
            flash("Ten film jest już na Twojej liście.")
            return render_template("add_movie.html", title=title)

        db.execute("INSERT INTO movies(title, year, poster_url, is_watched) VALUES (?, ?, ?, ?)", [real_title, year, poster_url, 0])
        db.commit()
        flash(f"Pomyślnie dodano film: {real_title}!")
        return redirect(url_for("web.list_movies"))
        
    return render_template("add_movie.html")

@web.route("/movies/<int:movie_id>/status", methods=["POST"])
def update_movies_status(movie_id):
    db = get_db()
    db.execute("UPDATE movies SET is_watched = NOT is_watched WHERE id = ?", [movie_id])
    db.commit()
    
    view_name = request.form.get("view_name")
    flash("Zaktualizowano status filmu.")
    
    if view_name == "task":
        return redirect(url_for("web.movie", movie_id=movie_id))
    return redirect(url_for("web.list_movies"))

@web.route("/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(movie_id):
    db = get_db()
    db.execute("DELETE FROM movies WHERE id = ?", [movie_id])
    db.commit()
    flash("Usunięto film z listy.")
    return redirect(url_for("web.list_movies"))