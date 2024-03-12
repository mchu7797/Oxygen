from flask import Blueprint, redirect, abort, g

from src.config import DATABASE_CONFIG
from src.database import DatabaseConnection

redirection = Blueprint("redirection", __name__)
database = DatabaseConnection(DATABASE_CONFIG)

def get_db():
    if 'db' not in g:
        g.db = DatabaseConnection(DATABASE_CONFIG)

    return g.db


@redirection.teardown_request
def teardown_db(_):
    db = g.pop('db', None)

    if db is not None:
        db.close()


@redirection.route("/p/<nickname>")
def redirect_to_player_page(nickname: str):
    player_id = get_db().utils.nickname_to_usercode(nickname)

    if player_id == -1:
        return abort(404)

    return redirect(f"/player-scoreboard/{player_id}/2"), 301


@redirection.route("/favicon.ico")
def return_favicon():
    return redirect("/static/favicon.ico"), 301
