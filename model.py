"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy
import correlation

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id,
                                               self.email)

    def similarity(self, other):
        """Return Pearson rating for user compared to other user."""

        # Build empty objects to hold data
        u_ratings = {}
        paired_ratings = []

        # Add movie_id & Rating object to dictionary
        for r in self.ratings:
            u_ratings[r.movie_id] = r

        # If other user has rated the same movie as current user, add scores to list
        for r in other.ratings:
            u_r = u_ratings.get(r.movie_id)
            if u_r:
                paired_ratings.append((u_r.score, r.score))

        # If crossover, return pearson correlation, else return 0.0
        if paired_ratings:
            return correlation.pearson(paired_ratings)
        else:
            return 0.0

    def predict_rating(self, movie):
        """Predict user's rating of a movie."""

        # Get all other ratings for the movie
        other_ratings = movie.ratings

        # Calculate correlation between this user and all other reviewing users
        similarities = [
            (self.similarity(r.user), r)
            for r in other_ratings
        ]

        # Sort by most to least similar
        similarities.sort(reverse=True)

        # Remove all anti-similarities
        similarities = [(sim, r) for sim, r in similarities
                        if sim > 0]

        # If there are not positive similarities, return None
        if not similarities:
            return None

        # Calculate predicted score using weighted mean
        numerator = sum([r.score * sim for sim, r in similarities])
        denominator = sum([sim for sim, r in similarities])

        return numerator/denominator


class Movie(db.Model):
    """Movie listings."""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    released_at = db.Column(db.DateTime, nullable=True)
    imbd_url = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Movie movie_id=%s title=%s>" % (self.movie_id,
                                                 self.title)


class Rating(db.Model):
    """Movie ratings by user"""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.movie_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    movie = db.relationship('Movie', backref=db.backref('ratings',
                                                        order_by=rating_id))
    user = db.relationship('User', backref=db.backref('ratings',
                                                      order_by=rating_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        s = "<Rating rating_id=%s movie_id=%s user_id=%s score=%s>"
        return s % (self.rating_id, self.movie_id, self.user_id,
                    self.score)

##############################################################################
# Helper functions


def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
