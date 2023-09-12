from flask import Blueprint, request, render_template, abort, redirect

from database import DatabaseConnection
from config import DATABASE_CONFIG
from tools.search_parser import parse_search

scoreboard = Blueprint("scoreboard", __name__)
database = DatabaseConnection(DATABASE_CONFIG)


@scoreboard.route("/online")
@scoreboard.route("/online-for-launcher")
def online():
    online_players = database.tools.get_online_players()
    return render_template("online.html", online=online_players)


@scoreboard.route("/music", methods=["GET"])
def music_find():
    keyword = request.args.get("keyword")

    if keyword is None:
        return render_template("find-music.html", song_list=[], init=True)

    result_data = database.tools.search_chart(parse_search(keyword))
    return render_template("find-music.html", song_list=result_data, init=False)


@scoreboard.route("/player-scoreboard/<player_code>")
def append_difficlty(player_code):
    return redirect(f"/player-scoreboard/{player_code}/2", code=301)


@scoreboard.route("/player-scoreboard/<player_code>/<difficulty>")
@scoreboard.route("/player-scoreboard/<player_code>/<difficulty>/<show_f_rank>")
def player_scoreboard(player_code, difficulty, show_f_rank="N"):
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
            info = database.scoreboard.get_player_ranking(category)
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

    ranking_data = database.scoreboard.get_playcount_ranking(top=top)

    return render_template("chart-ranking.html", ranking=ranking_data)
