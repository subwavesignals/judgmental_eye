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


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/register', methods=['GET', 'POST'])
def register_form():
    """Displays registration form as GET and handles input as POST"""

    if request.method == "GET":
        return render_template("registration_form.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")

        users = User.query.filter_by(email=email).all()

        if not users:
            user = User(email=email, password=password)

            db.session.add(user)
            db.session.commit()

            flash("User added.")
            return redirect("/")
        else:
            flash("User already exists in database.")
            return redirect("/register")


@app.route("/login", methods=['GET', 'POST'])
def login_form():
    """Display login form as GET and handles input as POST"""

    if request.method == "GET":

        if session.get('username') is not None:
            flash("You're already logged in as {}.".format(session.get('username')))
            return redirect("/")
        else:
            return render_template("login_form.html")

    else:
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            user = User.query.filter_by(email=email).one()
        except sqlalchemy.orm.exc.NoResultFound:   # specify exception type
            flash("Username not in database.")
            return redirect("/login")

        if user.password == password:
            session['username'] = user.email
            flash("Login successful.")
            return redirect("/")
        else:
            flash("Incorrect password.")
            return redirect("/login")


@app.route("/logout")
def logout():
    """Clear Flask session and log out."""

    session.clear()
    flash("Logged out.")
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
