from random import random

from flask import Blueprint, request, render_template, abort, redirect, g

from src.config import DATABASE_CONFIG
from src.database import DatabaseConnection
from src.database.player_ranking_manager import PlayerRankingOption
from src.tools.search_parser import parse_search

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
    online_players = get_db().utils.get_online_players()
    return render_template("online.html", online=online_players)


@scoreboard.route("/music", methods=["GET"])
def music_find():
    keyword = request.args.get("keyword")

    if keyword is None:
        return render_template("find-chart.html", song_list=[], init=True)

    result_data = get_db().utils.search_chart(parse_search(keyword))
    return render_template("find-chart.html", song_list=result_data, init=False)


@scoreboard.route("/player-scoreboard/<player_code>")
def append_difficulty(player_code):
    return redirect(f"/player-scoreboard/{player_code}/2", code=301)


@scoreboard.route("/player-scoreboard/<player_code>/<difficulty>")
def player_scoreboard(player_code, difficulty):
    show_f_rank = True if request.args.get("show-f-rank", type=int) == 1 else False
    show_recent = True if request.args.get("show-recent", type=int) == 1 else False
    page = request.args.get("page", type=int)

    if page is None:
        page = 0

    if show_recent:
        player_scores = get_db().player_ranking.get_recent_records(
            player_code, difficulty, show_f_rank
        )
    else:
        player_scores = get_db().player_ranking.get_player_top_records(
            player_code, difficulty, show_f_rank, page=page
        )

    player_metadata = get_db().info.get_player_info(player_code, difficulty)
    player_tiers = get_db().info.get_tier_info(player_code)
    player_score_count = get_db().player_ranking.get_player_top_records_count(player_code, difficulty, show_f_rank)


    if player_metadata is None:
        return abort(404)

    return render_template(
        "player.html",
        scoreboard=player_scores,
        metadata=player_metadata,
        tier=player_tiers,
        show_f_rank=show_f_rank,
        show_recent=show_recent,
        page=page,
        max_page=int(player_score_count / 100)
    )


@scoreboard.route("/music-scoreboard/<music_code>")
@scoreboard.route("/music-scoreboard/<music_code>/<difficulty>")
def music_scoreboard(music_code, difficulty=2):
    if music_code is None:
        return abort(404)

    music_scores = get_db().chart_ranking.get_chart_top_records(music_code, difficulty)
    music_metadata = get_db().info.get_music_info(music_code, difficulty)
    url_before = request.headers.get("referer")

    if music_metadata is None:
        return abort(404)

    return render_template(
        "chart.html",
        scoreboard=music_scores,
        metadata=music_metadata,
        referer=url_before
    )


@scoreboard.route("/ranking/player")
@scoreboard.route("/ranking/player/<int:ranking_category>")
def player_ranking(ranking_category=7):
    try:
        if 0 <= ranking_category <= 8:
            info = get_db().player_ranking.get_player_ranking(ranking_category)
            return render_template(
                "player-ranking.html",
                status=info["player_infos"],
                category_name=info["current_option_name"],
                category_code=ranking_category
            )

        return abort(404)
    except ValueError:
        return abort(404)


@scoreboard.route("/ranking/chart")
def chart_ranking():
    top = request.args.get("top")
    date_start = request.args.get("date_start")
    date_end = request.args.get("date_end")

    if top is None:
        top = 200

    if date_start is None and date_end is None:
        ranking_data = get_db().chart_ranking.get_play_count_ranking(top=top)
    else:
        try:
            ranking_data = get_db().chart_ranking.get_play_count_ranking(top=top, day_start=date_start, day_end=date_end)
        except ValueError:
            ranking_data = []

    return render_template("chart-ranking.html", ranking=ranking_data)


@scoreboard.route("/history", methods=["GET"])
def history():
    player_id = request.args.get("player_id", type=int)
    chart_id = request.args.get("chart_id", type=int)
    gauge_difficulty = request.args.get("gauge_difficulty", type=int)
    order_by_date = request.args.get("order_by_date", False, type=lambda value: value == "true")

    if player_id is None or chart_id is None:
        abort(404)

    if gauge_difficulty is None:
        gauge_difficulty = 2

    histories = get_db().player_ranking.get_record_histories(
        player_id, chart_id, gauge_difficulty, order_by_date=order_by_date
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
        order_by_date=order_by_date
    )

@scoreboard.route("/ranking/best_play/<int:player_id>")
def best_play_ranking(player_id):
    sort_option = request.args.get("sort_option", type=int)

    if sort_option is None:
        sort_option = PlayerRankingOption.ORDER_CLEAR

    ranking_data = get_db().player_ranking.get_best_play(player_id, PlayerRankingOption(sort_option))

    return render_template("best-play.html", scoreboard=ranking_data)