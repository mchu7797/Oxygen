import json
from flask import Flask, request, render_template, abort, redirect
from flask_cors import CORS

from models.database import OxygenDatabase
from config import DATABASE_CONFIG
from tools.search_parser import parse_search

app = Flask(__name__)
CORS(app)

db = OxygenDatabase(DATABASE_CONFIG)

ROBOTS_TXT_DATA = """
User-agent: *
Disallow: /
Allow: /$
"""


@app.errorhandler(403)
def handle_403():
    return render_template("error.html"), 403


@app.errorhandler(404)
def handle_404():
    return render_template("error.html"), 404


@app.errorhandler(500)
def handle_500():
    return render_template("error.html"), 500


@app.route("/robots.txt")
def robots():
    return ROBOTS_TXT_DATA


@app.route("/favicon.ico")
def favicon():
    return ""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/online")
@app.route("/online-for-launcher")
def online():
    online_players = db.utils.get_online_players()
    return render_template("online.html", online=online_players)


@app.route("/api/online_players")
def api_get_online():
    online_players = db.utils.get_online_players()
    return json.dumps(online_players, ensure_ascii=False)


@app.route("/troubleshoot")
def show_troubleshoot():
    return render_template("troubleshoot.html")


@app.route("/troubleshoot/fix-login", methods=["POST"])
def fix_login():
    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    db.utils.clean_login_data(player_id, password)
    return render_template("troubleshoot.html", fix_success=True)


@app.route("/troubleshoot/gem-to-cash", methods=["POST"])
def gem_to_cash():
    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    exchange_rate = int(request.form.get("gem-amount"))

    result = db.utils.exchange_cash(player_id, password, exchange_rate)

    if result == 3:
        wallet = db.utils.get_wallet_info(id)
    else:
        wallet = None

    return render_template("troubleshoot.html", gtc_result=result, wallet=wallet)


@app.route("/music", methods=["GET"])
def music_find():
    keyword = request.args.get("keyword")

    if keyword is None:
        return render_template("find-music.html", song_list=[], init=True)

    result_data = db.utils.search_chart(parse_search(keyword))
    return render_template("find-music.html", song_list=result_data, init=False)


@app.route("/player-scoreboard/<player_code>")
def append_difficlty(player_code):
    return redirect(f"/player-scoreboard/{player_code}/2", code=301)


@app.route("/player-scoreboard/<player_code>/<difficulty>")
@app.route("/player-scoreboard/<player_code>/<difficulty>/<show_f_rank>")
def player_scoreboard(player_code, difficulty, show_f_rank="F"):
    show_f_rank = True if show_f_rank == "F" else False
    player_scores = db.scoreboard.get_player_scoreboard(
        player_code, difficulty, show_f_rank
    )
    player_metadata = db.information.get_player_info(player_code, difficulty)
    player_tiers = db.information.get_tier_info(player_code)

    if player_metadata is None:
        return abort(404)

    return render_template(
        "player.html",
        scoreboard=player_scores,
        metadata=player_metadata,
        tier=player_tiers,
    )


@app.route("/p/<nickname>")
def nick_to_user(nickname):
    player_id = db.utils.nickname_to_usercode(nickname)

    if player_id == -1:
        return abort(404)

    return redirect(f"/player-scoreboard/{player_id}/2", code=301)


@app.route("/music-scoreboard/<music_code>")
@app.route("/music-scoreboard/<music_code>/<difficulty>")
def music_scoreboard(music_code, difficulty=2):
    if music_code is None:
        return abort(404)

    music_scores = db.scoreboard.get_music_scoreboard(music_code, difficulty)
    music_metadata = db.information.get_music_info(music_code, difficulty)

    if music_metadata is None:
        return abort(404)

    return render_template(
        "music.html", scoreboard=music_scores, metadata=music_metadata
    )


@app.route("/ranking")
@app.route("/ranking/<ranking_category>")
def ranking(ranking_category=7):
    try:
        category = int(ranking_category)
        if 0 <= category <= 8:
            info = db.scoreboard.get_player_ranking(category)
            return render_template(
                "ranking.html",
                status=info["player_infos"],
                category_name=info["current_option_name"],
            )

        return abort(404)
    except ValueError:
        return abort(404)


if __name__ == "__main__":
    app.run(debug=True)
    """
    from gevent.pywsgi import WSGIServer

    SSL_KEY = "C:\\ServerPackage\\Scoreboard\\Certification\\dpjam.net-key.pem"
    SSL_CERT = "C:\\ServerPackage\\Scoreboard\\Certification\\dpjam.net-chain.pem"

    http_server = WSGIServer(("0.0.0.0", 443), app, keyfile=SSL_KEY, certfile=SSL_CERT)
    http_server.serve_forever()
    """
