''' agendawfe controller '''
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from agendawfe.auth import login_required
from agendawfe.db import get_db

bp = Blueprint("agenda", __name__)


@bp.route("/")
@login_required
def index():
    """Show all the posts, most recent first."""
    db_connection = get_db()
    sql = ("SELECT p.id, title, body, created, author_id, username" +
          " FROM post p JOIN user u ON p.author_id = u.id" +
          " where u.id = "  + str(g.user['id']) +
          " ORDER BY created DESC")
    posts = db_connection.execute(sql).fetchall()
    return render_template("agenda/index.html", posts=posts)


def get_post(agenda_item_id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (agenda_item_id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db_connection = get_db()
            db_connection.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db_connection.commit()
            return redirect(url_for("agenda.index"))

    return render_template("agenda/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db_connection = get_db()
            db_connection.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db_connection.commit()
            return redirect(url_for("agenda.index"))

    return render_template("agenda/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db_connection = get_db()
    db_connection.execute("DELETE FROM post WHERE id = ?", (id,))
    db_connection.commit()
    return redirect(url_for("agenda.index"))
