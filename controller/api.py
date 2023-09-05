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
    pass


@api.route("/scoreboard/chart/<int:chart_id>", methods=["GET"])
def get_chart_scoreboard(chart_id):
    gauge_difficulty = request.args.get(
        "gauge_difficulty",
    )

    esponse_data = {}
    response_data["scores"] = database.scoreboard.get_music_scoreboard(chart_id, 2)
    response_data["chart_info"] = database.info.get_music_inf


@api.route("/chart/<int:chart_id>", methods=["GET"])
def get_chart(chart_id):
    pass


@api.route("/player/<int:player_id>", methods=["GET"])
def get_player(player_id):
    pass


@api.route("/player")
def get_all_player():
    pass


@api.route("/chart")
def get_all_charts():
    pass
