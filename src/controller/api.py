from flask import Blueprint, request, abort, json, make_response, g

from src.config import DATABASE_CONFIG
from src.database import DatabaseConnection
from src.database.player_ranking_manager import PlayerRankingOption

api = Blueprint("api", __name__, url_prefix="/api")


def get_db():
    if "db" not in g:
        g.db = DatabaseConnection(DATABASE_CONFIG)

    return g.db


@api.teardown_request
def teardown_db(_):
    db = g.pop("db", None)

    if db is not None:
        db.close()


@api.route("/online_players")
@api.route("/userlist")
@api.route("/player/online")
def get_online():
    response = make_response(
        json.dumps(get_db().utils.get_online_players(), ensure_ascii=False)
    )

    response.headers["Content-Type"] = "application/json"

    return response


@api.route("/login_v2", methods=["POST"])
@api.route("/player/login", methods=["POST"])
def check_login():
    request_data = request.get_json()

    user_id = request_data["username"]

    password = request_data["password"]

    if user_id is None or password is None:
        abort(400)

    login_token = get_db().utils.generate_login_token(user_id, password)

    if login_token is None:
        abort(403)

    return login_token


# Below four endpoint has argument as query string
# gauge_difficulty : If you set this argument, result only shows selected gauge difficulty
@api.route("/scoreboard/player/<int:player_id>", methods=["GET"])
def get_scoreboard_by_player(player_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)
    show_f_rank = request.args.get("show-f-rank", type=bool)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    if show_f_rank is None:
        show_f_rank = True

    player_scoreboard = get_db().player_ranking.get_player_top_records(
        player_id, gauge_difficulty, show_f_rank
    )

    if player_scoreboard is None:
        abort(404)

    return make_json_response(player_scoreboard)


@api.route("/scoreboard/player/<int:player_id>/recent", methods=["GET"])
def get_recent_records_by_player(player_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    recent_records = get_db().player_ranking.get_recent_records(
        player_id, gauge_difficulty
    )

    if recent_records is None:
        abort(404)

    return make_json_response(recent_records)


@api.route("/scoreboard/chart/<int:chart_id>", methods=["GET"])
def get_scoreboard_by_chart(chart_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    chart_scoreboard = get_db().chart_ranking.get_chart_top_records(
        chart_id, gauge_difficulty
    )

    if chart_scoreboard is None:
        abort(404)

    return make_json_response(chart_scoreboard)


@api.route("/scoreboard/history", methods=["GET"])
def get_record_histories():
    player_id = request.args.get("player_id", type=int)
    chart_id = request.args.get("chart_id", type=int)
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if player_id is None or chart_id is None:
        abort(404)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    histories = get_db().player_ranking.get_record_histories(
        player_id, chart_id, gauge_difficulty
    )

    return make_json_response(histories)


@api.route("/chart/<int:chart_id>", methods=["GET"])
def get_chart(chart_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    music_info = get_db().info.get_music_info(chart_id, gauge_difficulty)

    if music_info is None:
        abort(404)

    return make_json_response(music_info)


@api.route("/player/<int:player_id>", methods=["GET"])
def get_player(player_id):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    player_info = get_db().info.get_player_info(player_id, gauge_difficulty)

    if player_info is None:
        abort(404)

    return make_json_response(
        get_db().info.get_player_info(player_id, gauge_difficulty)
    )


@api.route("/player/<nickname>", methods=["GET"])
def get_player_by_nickname(nickname):
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    player_id = get_db().utils.nickname_to_usercode(nickname)
    player_info = get_db().info.get_player_info(player_id, gauge_difficulty)

    if player_info is None:
        abort(404)

    return make_json_response(
        get_db().info.get_player_info(player_id, gauge_difficulty)
    )


@api.route("/chart/ranking")
def get_chart_ranking():
    top = request.args.get("top", type=int)

    if top is None:
        top = 200

    return make_json_response(get_db().chart_ranking.get_play_count_ranking(top=top))


@api.route("/players")
def get_all_player():
    return make_json_response(
        get_db().player_ranking.get_player_ranking(
            PlayerRankingOption.ORDER_CLEAR
        )
    )


@api.route("/charts")
def get_all_charts():
    empty_search_request = {
        "keywords": "",
        "options": {"level": [0, 180], "title": True, "artist": True, "mapper": True},
    }

    return make_json_response(get_db().utils.search_chart(empty_search_request))


def make_json_response(data):
    response = make_response(json.dumps(data, ensure_ascii=False, default=str))
    response.headers["Content-Type"] = "application/json"

    return response
