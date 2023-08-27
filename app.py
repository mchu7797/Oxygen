import json
from flask import Flask, render_template, abort, url_for
from flask_cors import CORS

from controller.api import api
from controller.redirection import redirection
from controller.troubleshoot import troubleshoot
from controller.scoreboard import scoreboard

app = Flask(__name__)

app.register_blueprint(api)
app.register_blueprint(redirection)
app.register_blueprint(troubleshoot)
app.register_blueprint(scoreboard)

CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/robots.txt")
def robots():
    return "User-Agent: *\nDisallow: /"


@app.route("/")
def index():
    return render_template("index.html")
