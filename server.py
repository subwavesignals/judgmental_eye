"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from model import (User, Rating, Movie, connect_to_db, db)
from flask_sqlalchemy import sqlalchemy


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "jhdwfjdsufdsjkfdhugsnotdrugsdsubyegd"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined

BERATEMENT_MESSAGES = [
    "I suppose you don't have such bad taste after all.",
    "I regret every decision that I've ever made that has brought me to listen to your opinion.",
    "Words fail me, as your taste in movies has clearly failed you.",
    "That movie is great. For a clown to watch. Idiot.",
    "Words cannot express the awfulness of your taste."
    ]


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/users/<user_id>')
def display_user(user_id):
    """Displays details for specified user."""

    user = User.query.filter_by(user_id=user_id).one()
    return render_template("user_details.html", user=user)


@app.route("/movies")
def movie_list():
    """Show list of movies ordered by title"""

    movies = Movie.query.order_by('title').all()
    return render_template("movie_list.html", movies=movies)


@app.route('/movies/<movie_id>', methods=['GET', 'POST'])
def display_movie(movie_id):
    """Displays details for specified movie and allow user to add rating."""

    # Prevents unlogged in users from adding ratings
    user_has_rated = None

    # Find current user if logged in
    if session.get('username'):
        user_id = session.get('user_id')

        # Determine if user has previously rated this movie
        user_has_rated = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).first()

    # Return movie ratings on GET request
    if request.method == 'GET':
        movie = Movie.query.filter_by(movie_id=movie_id).first()
        rating_scores = [r.score for r in movie.ratings]

        avg_rating = float(sum(rating_scores)) / len(rating_scores)

        prediction = None

        if (not user_has_rated) and user_id:
            user = User.query.get(user_id)
            if user:
                prediction = user.predict_rating(movie)

        # Either use the prediction or their real rating
        if prediction:

            # User hasn't scored; use our prediction if we made one
            effective_rating = prediction

        elif user_has_rated:

            # User has already scored for real; use that
            effective_rating = user_has_rated.score

        else:

            # User hasn't scored, and we couldn't get a prediction
            effective_rating = None

        # Get the eye's rating, either by predicting or using real rating

        the_eye = (User.query.filter_by(email="the-eye@of-judgment.com")
                             .first())
        eye_rating = Rating.query.filter_by(
            user_id=the_eye.user_id, movie_id=movie.movie_id).first()

        if eye_rating is None:
            eye_rating = the_eye.predict_rating(movie)

        else:
            eye_rating = eye_rating.score

        if eye_rating and effective_rating:
            difference = abs(eye_rating - effective_rating)

        else:
            # We couldn't get an eye rating, so we'll skip difference
            difference = None

        if difference is not None:
            beratement = BERATEMENT_MESSAGES[int(difference)]

        else:
            beratement = None

        return render_template("movie_details.html",
                               movie=movie,
                               user_has_rated=user_has_rated,
                               average=avg_rating,
                               prediction=prediction,
                               beratement=beratement)

    # Handle new movie rating on POST request
    else:
        # Get form input
        score = request.form.get("score")

        # If user has already rated, update the score
        if user_has_rated:
            user_has_rated.score = score

        # Else add new rating to database
        else:
            rating = Rating(movie_id=movie_id, user_id=user_id, score=score)
            db.session.add(rating)

        # Commit changes to database
        db.session.commit()

        flash("Your rating of {} has been added.".format(score))
        return redirect("/movies/" + movie_id)


@app.route('/register', methods=['GET', 'POST'])
def register_form():
    """Displays registration form as GET and handles input as POST"""

    # Return registration form on GET request
    if request.method == "GET":
        return render_template("registration_form.html")

    # Handle registration form submission on POST request
    else:

        # Get form inputs
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if username already in database
        users = User.query.filter_by(email=email).first()

        # If not, add username and redirect to homepage
        if not users:
            user = User(email=email, password=password)

            db.session.add(user)
            db.session.commit()

            flash("User added.")
            return redirect("/")

        # Else inform user that username already exists
        else:
            flash("User already exists in database.")
            return redirect("/register")


@app.route("/login", methods=['GET', 'POST'])
def login_form():
    """Display login form as GET and handles input as POST"""

    # Return login form on GET request
    if request.method == "GET":

        # If user is already logged in, inform and redirect to homepage
        if session.get('username'):
            flash("You're already logged in as {}.".format(session.get('username')))
            return redirect("/")

        # Else display login form
        else:
            return render_template("login_form.html")

    # Handle login form submission on POST request
    else:

        # Get form inputs
        email = request.form.get("email")
        password = request.form.get("password")

        # Check to see if username in database, catch sqla error
        try:
            user = User.query.filter_by(email=email).one()
        except sqlalchemy.orm.exc.NoResultFound:
            flash("Username not in database.")
            return redirect("/login")

        # Check for correct password, set session, and redirect to homepage
        if user.password == password:
            session['username'] = user.email
            session['user_id'] = user.user_id

            flash("Login successful.")
            return redirect("/users/" + str(user.user_id))

        # Inform user of incorrect password
        else:
            flash("Incorrect password.")
            return redirect("/login")


@app.route("/logout")
def logout():
    """Clear Flask session and log out."""

    # If no user logged in, don't log out; otherwise clear session
    if session.get('username'):
        session.clear()
        flash("Logged out.")
    else:
        flash("No user currently logged in.")

    return redirect("/")

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
