from flask import Blueprint, render_template, request, g

from config import DATABASE_CONFIG
from database import DatabaseConnection

troubleshoot = Blueprint("troubleshoot", __name__, url_prefix="/troubleshoot")


def get_db():
    if 'db' not in g:
        g.db = DatabaseConnection(DATABASE_CONFIG)

    return g.db


@troubleshoot.teardown_request
def teardown_db(_):
    db = g.pop('db', None)

    if db is not None:
        db.close()


@troubleshoot.route("/fix-login", methods=["POST", "GET"])
def fix_login():
    if request.method == "GET":
        return render_template("fix-connection.html")

    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    get_db().tools.clean_login_data(player_id, password)
    return render_template("fix-connection.html", fix_success=True)


@troubleshoot.route("/cash-to-gem", methods=["POST", "GET"])
def cash_to_gem():
    database = get_db()

    if request.method == "GET":
        return render_template("cash-to-gem.html", wallet=None)

    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    exchange_rate = int(request.form.get("gem-amount"))

    result = database.tools.exchange_cash(player_id, password, exchange_rate, "gem")
    wallet = database.tools.get_wallet_info(player_id)

    return render_template("cash-to-gem.html", gtc_result=result, wallet=wallet)


@troubleshoot.route("/gem-to-cash", methods=["POST", "GET"])
def gem_to_cash():
    database = get_db()

    if request.method == "GET":
        return render_template("gem-to-cash.html", wallet=None)

    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    exchange_rate = int(request.form.get("gem-amount"))

    result = database.tools.exchange_cash(player_id, password, exchange_rate, "mcash")
    wallet = database.tools.get_wallet_info(player_id)

    return render_template("gem-to-cash.html", gtc_result=result, wallet=wallet)
