import json

from flask import Blueprint, request, abort
from flask_cors import CORS

from database import DatabaseConnection
from config import DATABASE_CONFIG

api = Blueprint("api", __name__, url_prefix="/api")

database = DatabaseConnection(DATABASE_CONFIG)


# Old Method
@api.route("/online_players")
# New Method
@api.route("/userlist")
@api.route("/player/online")
def get_online():
    online_players = database.tools.get_online_players()
    return json.dumps(online_players, ensure_ascii=False)


@api.route("/login", methods=["POST"])
@api.route("/player/login", methods=["POST"])
def check_login():
    request_data = request.get_json()

    user_id = request_data["username"]
    password = request_data["password"]

    if user_id is None or password is None:
        abort(400)

    login_token = database.tools.generate_login_token(user_id, password)

    if login_token is None:
        abort(404)

    return login_token


# Below four endpoint has argument as query string
# gauge_difficulty : If you set this argument, result only shows selected gauge difficulty


@api.route("/scoreboard/player/<int:player_id>", methods=["GET"])
def get_player_scoreboard(player_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)
    show_f_rank = request.args.get("show-f-rank", type=bool)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    if show_f_rank is None:
        show_f_rank = True

    return json.dumps(
        database.scoreboard.get_player_scoreboard(
            player_id, gauge_difficulty, show_f_rank
        ),
        ensure_ascii=False,
        default=str,
    )


@api.route("/scoreboard/chart/<int:chart_id>", methods=["GET"])
def get_chart_scoreboard(chart_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    return json.dumps(
        database.scoreboard.get_music_scoreboard(chart_id, gauge_difficulty),
        ensure_ascii=False,
        default=str,
    )


@api.route("/chart/<int:chart_id>", methods=["GET"])
def get_chart(chart_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    return json.dumps(
        database.info.get_music_info(chart_id, gauge_difficulty),
        ensure_ascii=False,
        default=str,
    )


@api.route("/player/<int:player_id>", methods=["GET"])
def get_player(player_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    return json.dumps(
        database.info.get_player_info(player_id, gauge_difficulty),
        ensure_ascii=False,
        default=str,
    )


@api.route("/players")
def get_all_player():
    return json.dumps(
        database.scoreboard.get_player_ranking(7), ensure_ascii=False, default=str
    )


@api.route("/charts")
def get_all_charts():
    empty_search_request = {
        "keywords": "",
        "options": {"level": [0, 180], "title": True, "artist": True, "mapper": True},
    }

    return json.dumps(database.tools.search_chart(), ensure_ascii=False, default=str)
