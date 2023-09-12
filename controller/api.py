from flask import Blueprint, request, abort, json, make_response

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

    response = make_response(json.dumps(online_players, ensure_ascii=False))

    response.headers["Content-Type"] = "application/json"

    return response


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

    player_scoreboard = database.scoreboard.get_player_scoreboard(
        player_id, gauge_difficulty, show_f_rank
    )

    if player_scoreboard is None:
        abort(404)

    return make_json_response(player_scoreboard)


@api.route("/scoreboard/chart/<int:chart_id>", methods=["GET"])
def get_chart_scoreboard(chart_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    chart_scoreboard = database.scoreboard.get_music_scoreboard(
        chart_id, gauge_difficulty
    )

    if chart_scoreboard is None:
        abort(404)

    return make_json_response(chart_scoreboard)


@api.route("/chart/<int:chart_id>", methods=["GET"])
def get_chart(chart_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    music_info = database.info.get_music_info(chart_id, gauge_difficulty)

    if music_info is None:
        abort(404)

    return make_json_response(music_info)


@api.route("/player/<int:player_id>", methods=["GET"])
def get_player(player_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    player_info = database.info.get_player_info(player_id, gauge_difficulty)

    if player_info is None:
        abort(404)

    return make_json_response(
        database.info.get_player_info(player_id, gauge_difficulty)
    )


@api.route("/player/<nickname>", methods=["GET"])
def get_player_by_nickname(nickname):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    player_id = database.tools.nickname_to_usercode(nickname)
    player_info = database.info.get_player_info(player_id, gauge_difficulty)

    if player_info is None:
        abort(404)

    return make_json_response(
        database.info.get_player_info(player_id, gauge_difficulty)
    )


@api.route("/chart/ranking")
def get_chart_ranking():
    top = request.args.get("top", type=int)

    if top is None:
        top = 200

    return make_json_response(database.scoreboard.get_playcount_ranking(top=top))


@api.route("/players")
def get_all_player():
    return make_json_response(database.scoreboard.get_player_ranking(7))


@api.route("/charts")
def get_all_charts():
    empty_search_request = {
        "keywords": "",
        "options": {"level": [0, 180], "title": True, "artist": True, "mapper": True},
    }

    return make_json_response(database.tools.search_chart(empty_search_request))


def make_json_response(data):
    response = make_response(json.dumps(data, ensure_ascii=False, default=str))
    response.headers["Content-Type"] = "application/json"

    return response
