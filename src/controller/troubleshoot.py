from flask import Blueprint, render_template, request, g, redirect, url_for

from config import DATABASE_CONFIG
from tools.mail import send_password_reset_mail
from database import DatabaseConnection

troubleshoot = Blueprint("troubleshoot", __name__, url_prefix="/troubleshoot")


def get_db():
    if "db" not in g:
        g.db = DatabaseConnection(DATABASE_CONFIG)

    return g.db


@troubleshoot.teardown_request
def teardown_db(_):
    db = g.pop("db", None)

    if db is not None:
        db.close()


@troubleshoot.route("/fix-login", methods=["POST", "GET"])
def fix_login():
    if request.method == "GET":
        return render_template("fix-connection.html")

    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    get_db().utils.clean_login_data(player_id, password)
    return render_template("fix-connection.html", fix_success=True)


@troubleshoot.route("/cash-to-gem", methods=["POST", "GET"])
def cash_to_gem():
    database = get_db()

    if request.method == "GET":
        return render_template("cash-to-gem.html", wallet=None)

    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    exchange_rate = int(request.form.get("gem-amount"))

    result = database.utils.exchange_cash(player_id, password, exchange_rate, "gem")
    wallet = database.utils.get_wallet_info(player_id)

    return render_template("cash-to-gem.html", gtc_result=result, wallet=wallet)


@troubleshoot.route("/gem-to-cash", methods=["POST", "GET"])
def gem_to_cash():
    database = get_db()

    if request.method == "GET":
        return render_template("gem-to-cash.html", wallet=None)

    player_id = request.form.get("o2jam-id")
    password = request.form.get("o2jam-pw")
    exchange_rate = int(request.form.get("gem-amount"))

    result = database.utils.exchange_cash(player_id, password, exchange_rate, "mcash")
    wallet = database.utils.get_wallet_info(player_id)

    return render_template("gem-to-cash.html", gtc_result=result, wallet=wallet)


# Status on reset-password and reset-password-phase-2
# 0 : Send email
# 1 : Get new password
# 2 : Reset success
# 3 : ERROR Send email
# 4 : ERROR Get new password


@troubleshoot.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if request.method == "GET":
        return render_template("reset-password.html", status=0)
    else:
        account_id = request.values.get("account-id")

        if account_id is None:
            return render_template(
                "reset-password.html",
                status=3,
                error_message="Cannot found your id!",
            )

        database = get_db()

        token_id = database.utils.get_password_reset_token(account_id)
        email = database.utils.get_player_email(account_id)

        if token_id is None or email is None:
            return render_template(
                "reset-password.html",
                status=3,
                error_message="Cannot found your id!",
            )

        send_password_reset_mail(email, token_id)

        return redirect(url_for("troubleshoot.reset_password_phase_2"))


@troubleshoot.route("/reset-password-phase-2", methods=["GET", "POST"])
def reset_password_phase_2():
    if request.method == "GET":
        return render_template(
            "reset-password.html",
            status=1,
        )
    else:
        token_id = request.values.get("token-id")
        password = request.values.get("password")

        if token_id is None or password is None:
            return render_template(
                "reset-password.html",
                status=4,
                error_message="Token or password is invalid!",
            )

        database = get_db()

        if not database.utils.reset_password(token_id, password):
            return render_template(
                "reset-password.html",
                status=4,
                error_message="Token or password is invalid!",
            )

        return render_template(
            "reset-password.html",
            status=2,
        )
