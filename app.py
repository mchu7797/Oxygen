import json
from flask import Flask, render_template, abort
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
    return "User-Agent: *\nDisallow: /"


@app.route("/favicon.ico")
def fabicon():
    return abort(404)


@app.route("/")
def index():
    return render_template("index.html")
