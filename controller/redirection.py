from flask import Blueprint, redirect, abort

from database import DatabaseConnection
from config import DATABASE_CONFIG

redirection = Blueprint("redirection", __name__)
database = DatabaseConnection(DATABASE_CONFIG)


@redirection.route("/p/<nickname>")
def redirect_to_player_page(nickname: str):
    player_id = database.tools.nickname_to_usercode(nickname)

    if player_id == -1:
        return abort(404)

    return redirect(f"/player-scoreboard/{player_id}/2"), 301


@redirection.route("/favicon.ico")
def return_favicon():
    return redirect("/static/favicon.ico"), 301
