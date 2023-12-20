from flask import Blueprint, request, render_template, abort, redirect, g

from config import DATABASE_CONFIG
from database import DatabaseConnection
from tools.search_parser import parse_search

scoreboard = Blueprint("scoreboard", __name__)


def get_db():
    if "db" not in g:
        g.db = DatabaseConnection(DATABASE_CONFIG)

    return g.db


@scoreboard.teardown_request
def teardown_db(_):
    db = g.pop("db", None)

    if db is not None:
        db.close()


@scoreboard.route("/online")
@scoreboard.route("/online-for-launcher")
def online():
    online_players = get_db().tools.get_online_players()
    return render_template("online.html", online=online_players)


@scoreboard.route("/music", methods=["GET"])
def music_find():
    keyword = request.args.get("keyword")

    if keyword is None:
        return render_template("find-music.html", song_list=[], init=True)

    result_data = get_db().tools.search_chart(parse_search(keyword))
    return render_template("find-music.html", song_list=result_data, init=False)


@scoreboard.route("/player-scoreboard/<player_code>")
def append_difficulty(player_code):
    return redirect(f"/player-scoreboard/{player_code}/2", code=301)


@scoreboard.route("/player-scoreboard/<player_code>/<difficulty>")
@scoreboard.route("/player-scoreboard/<player_code>/<difficulty>/<show_f_rank>")
def player_scoreboard(player_code, difficulty, show_f_rank="N"):
    database = get_db()

    show_f_rank = True if show_f_rank == "Y" else False
    player_scores = database.scoreboard.get_player_scoreboard(
        player_code, difficulty, show_f_rank
    )
    player_metadata = database.info.get_player_info(player_code, difficulty)
    player_tiers = database.info.get_tier_info(player_code)

    if player_metadata is None:
        return abort(404)

    return render_template(
        "player.html",
        scoreboard=player_scores,
        metadata=player_metadata,
        tier=player_tiers,
    )


@scoreboard.route("/music-scoreboard/<music_code>")
@scoreboard.route("/music-scoreboard/<music_code>/<difficulty>")
def music_scoreboard(music_code, difficulty=2):
    database = get_db()

    if music_code is None:
        return abort(404)

    music_scores = database.scoreboard.get_music_scoreboard(music_code, difficulty)
    music_metadata = database.info.get_music_info(music_code, difficulty)

    if music_metadata is None:
        return abort(404)

    return render_template(
        "music.html", scoreboard=music_scores, metadata=music_metadata
    )


@scoreboard.route("/ranking/player")
@scoreboard.route("/ranking/player/<ranking_category>")
def player_ranking(ranking_category=7):
    try:
        category = int(ranking_category)
        if 0 <= category <= 8:
            info = get_db().scoreboard.get_player_ranking(category)
            return render_template(
                "player-ranking.html",
                status=info["player_infos"],
                category_name=info["current_option_name"],
            )

        return abort(404)
    except ValueError:
        return abort(404)


@scoreboard.route("/ranking/chart")
def chart_ranking():
    top = request.args.get("top")

    if top is None:
        top = 200

    ranking_data = get_db().scoreboard.get_playcount_ranking(top=top)

    return render_template("chart-ranking.html", ranking=ranking_data)


@scoreboard.route("/history", methods=["GET"])
def history():
    player_id = request.args.get("player_id", type=int)
    chart_id = request.args.get("chart_id", type=int)
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)

    if player_id is None or chart_id is None:
        abort(404)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    histories = get_db().scoreboard.get_record_histories(
        player_id, chart_id, gauge_difficulty
    )

    chart_data = get_db().info.get_music_info(chart_id, gauge_difficulty)
    player_data = get_db().info.get_player_info(player_id, gauge_difficulty)

    return render_template(
        "player-history.html",
        histories=histories,
        player_info=player_data,
        chart_info=chart_data,
        player_id=player_id,
        gauge_difficulty=gauge_difficulty,
    )
