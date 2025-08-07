from flask import Flask, render_template
from flask_cors import CORS

from src.config import CORS_ORIGINS
from src.controller.api import api
from src.controller.redirection import redirection
from src.controller.scoreboard import scoreboard
from src.controller.troubleshoot import troubleshoot

app = Flask(__name__)

app.register_blueprint(api)
app.register_blueprint(redirection)
app.register_blueprint(troubleshoot)
app.register_blueprint(scoreboard)

CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})


@app.route("/robots.txt")
def robots():
    return "User-Agent: *\nDisallow: /"


@app.route("/")
def index():
    return render_template("index.html")
