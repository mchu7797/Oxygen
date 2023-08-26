import json

from flask import Blueprint, request, abort
from flask_cors import CORS

from database import DatabaseConnection
from config import DATABASE_CONFIG

api = Blueprint("api", __name__, url_prefix="/api")

database = DatabaseConnection(DATABASE_CONFIG)


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

    return db.tools.generate_login_token(user_id, password)
