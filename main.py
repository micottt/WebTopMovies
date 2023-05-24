from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


class TopMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'Movie {self.title}'


with app.app_context():
    db.create_all()

    # new_movie = Movie(
    #     title="Phone Booth",
    #     year=2002,
    #     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    #     rating=7.3,
    #     ranking=10,
    #     review="My favourite character was the caller.",
    #     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    # )
    #
    # db.session.add(new_movie)
    # db.session.commit()


@app.route("/")
def home():
    with app.app_context():
        all_movies = TopMovie.query.order_by(TopMovie.rating).all()
        for i in range(len(all_movies)):
            all_movies[i].ranking = len(all_movies) - i
            db.session.commit()

        return render_template("index.html", movies=all_movies)


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")

    with app.app_context():
        movie = TopMovie.query.get(movie_id)
        if form.validate_on_submit():
            movie.rating = float(form.rating.data)
            movie.review = form.review.data
            db.session.commit()
            return redirect(url_for("home"))

    return render_template("edit.html", movie=movie, form=form)

    # if request.method == "POST":
    #     movie_id = request.form["id"]
    #
    #     with app.app_context():
    #         movie_to_update = Movie.query.get(movie_id)
    #         movie_to_update.ranking = request.form["rating"]
    #         movie_to_update.review = request.form["review"]
    #         db.session.commit()
    #     return redirect(url_for("home"))
    #
    # movie_id = request.args.get("id")
    # with app.app_context():
    #     movie_selected = Movie.query.get(movie_id)
    # return render_template("edit.html", movie=movie_selected)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")

    with app.app_context():
        movie = TopMovie.query.get(movie_id)
        db.session.delete(movie)
        db.session.commit()
        return redirect(url_for("home"))


class SearchMovieForm(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")


API_KEY = "c7d8a97ec127a3db4dae84dcd75d637a"
MOVIE_URL = "https://api.themoviedb.org/3/search/movie"


@app.route("/add", methods=["GET", "POST"])
def add():
    form = SearchMovieForm()

    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(MOVIE_URL, params={"api_key": API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)

    return render_template("add.html", form=form)


MOVIE_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_IMG_URL = "https://image.tmdb.org/t/p/w500"


@app.route("/find")
def find():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = TopMovie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_IMG_URL}{data['poster_path']}",
            description=data["overview"]
        )

        with app.app_context():
            db.session.add(new_movie)
            db.session.commit()
            return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
