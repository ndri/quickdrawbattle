import configparser
import datetime
import os
import random
import uuid

import simplejson as json
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from quickdraw import QuickDrawData
from sqlalchemy import func, cast, Float

config = configparser.ConfigParser()
config.read_file(open("config.ini"))
z = config["general"].getfloat("confidence_z")  # 1.96 => 0.975 confidence

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
app.secret_key = os.urandom(32)

db = SQLAlchemy(app)
qd = QuickDrawData(cache_dir=config["general"]["dataset_dir"], print_messages=False)


def uuid_gen() -> str:
    return str(uuid.uuid4()).replace("-", "")


# https://www.evanmiller.org/how-not-to-sort-by-average-rating.html
def ci_lower_bound(pos, neg):
    n = pos + neg
    if n == 0:
        return 0
    return ((pos + z ** 2 / 2) / n - z * ((pos * neg) / n + z ** 2 / 4) ** 0.5 / n) / (1 + z ** 2 / n)


# These are used to normalize the score to a range from 0 to 1
score_min = ci_lower_bound(1, config["general"].getint("vote_limit"))
score_max = ci_lower_bound(config["general"].getint("vote_limit") + 1, 0)


def calculate_score(ws, ls):  # wins, losses
    ws += 1  # Add hidden win, so drawings with 0 losses get a score bigger than 0
    n = cast(ws + ls, Float)  # Integer division in Postgres returns an integer
    score = ((ws + z ** 2 / 2) / n - z * func.sqrt((ws * ls) / n + z ** 2 / 4) / n) / (1 + z ** 2 / n)

    # Normalize score to a range from 0 to 1
    score = (score - score_min) / (score_max - score_min)

    return score


class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.String(16), nullable=False)
    category = db.Column(db.String)
    countrycode = db.Column(db.String)
    recognized = db.Column(db.Boolean)
    strokes = db.Column(db.String)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    votes = db.column_property(wins + losses)
    score = db.column_property(calculate_score(wins, losses))


class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(32), default=uuid_gen)
    ip = db.Column(db.String, default="")
    datetime = db.Column(db.DateTime, default=datetime.datetime.now)
    category = db.Column(db.String)
    drawing1 = db.Column(db.String(16))
    drawing2 = db.Column(db.String(16))
    result = db.Column(db.Integer, default=-1)  # -1 = not shown yet, 0 = shown but not voted, 1 and 2 are winners


@app.route("/")
def index():
    return render_template("index.html", categories=qd.drawing_names)


@app.route("/ranking")
def ranking():
    return render_template("ranking.html", categories=qd.drawing_names)


@app.route("/about")
def about():
    drawings = Drawing.query.count()
    battles = Battle.query.filter(Battle.result != 0).count()

    return render_template("about.html", drawings=drawings, battles=battles)


def get_new_drawing(category: str) -> Drawing:
    # Get new drawing until we find one that's not in the database yet
    while True:
        qd_drawing = qd.get_drawing(category)
        drawing = Drawing.query.filter_by(key_id=str(qd_drawing.key_id)).first()
        if not drawing:
            break

    # Add drawing to database and return it
    drawing = Drawing(
        key_id=str(qd_drawing.key_id),
        category=category,
        countrycode=qd_drawing.countrycode,
        recognized=qd_drawing.recognized,
        strokes=json.dumps(qd_drawing.strokes, separators=(',', ':'))
    )
    db.session.add(drawing)
    db.session.commit()

    return drawing


def get_random_drawing(category: str) -> Drawing:
    # If fewer than 25 drawings at or under 20 votes, return a new one
    drawings = Drawing.query.filter(
        Drawing.votes < config["general"].getint("vote_limit"),
        Drawing.category == category
    )
    if drawings.count() < config["general"].getint("drawing_limit"):
        return get_new_drawing(category)

    # Otherwise, return a random one from the database
    drawing = drawings.order_by(func.random()).first()

    return drawing


def get_new_battle(category: str) -> Battle:
    battle_drawings = []

    # Get 2 non-equal drawings
    while len(battle_drawings) < 2:
        potential_drawing = get_random_drawing(category)
        for drawing in battle_drawings:
            if drawing.key_id == potential_drawing.key_id:
                break
        else:
            battle_drawings.append(potential_drawing)

    # Make battle with the 2 drawings, add it to the database and return it
    battle = Battle(
        ip=request.remote_addr,
        category=category,
        drawing1=battle_drawings[0].key_id,
        drawing2=battle_drawings[1].key_id
    )
    db.session.add(battle)
    db.session.commit()

    return battle


def get_premade_battle(category: str) -> Battle:
    battle = Battle.query.filter_by(category=category, result=-1).first()

    # TODO: fill db with premade battles if they get under a certain amount
    # but I would have to check if they are still valid :s
    # will be easier with foreign key joins... TODO
    if not battle:
        return get_new_battle(category)

    return battle


def prepare_battle(category: str) -> dict:
    if category == "any" or category not in qd.drawing_names:
        category = random.choice(qd.drawing_names)

    new_battle = get_premade_battle(category)
    new_battle.result = 0  # Battle will not be picked anymore
    db.session.commit()

    return {
        "success": True,
        "id": new_battle.uuid,
        "category": category,
        "strokes1": json.loads(Drawing.query.filter_by(key_id=new_battle.drawing1).first().strokes),  # Should join
        "strokes2": json.loads(Drawing.query.filter_by(key_id=new_battle.drawing2).first().strokes)
    }


@app.route("/api/new_battle")
def api_new_battle():
    category = request.args.get("category", default="any", type=str)
    return jsonify(prepare_battle(category))


@app.route("/api/vote")
def api_vote():
    choice = request.args.get("choice", default="0", type=str)
    vote_uuid = request.args.get("battle", default="1337", type=str)
    category = request.args.get("category", default="any", type=str)

    if choice not in ("1", "2"):
        return jsonify(success=False, reason="Not a valid choice")

    battle = Battle.query.filter_by(uuid=vote_uuid).first()
    if not battle:
        return jsonify(success=False, reason="Not a valid battle")

    if battle.result in (1, 2):
        return jsonify(success=False, reason="Already voted")

    drawing1 = Drawing.query.filter_by(key_id=battle.drawing1).first()
    drawing2 = Drawing.query.filter_by(key_id=battle.drawing2).first()

    if choice == "1":
        drawing1.wins += 1
        drawing2.losses += 1
    else:
        drawing1.losses += 1
        drawing2.wins += 1

    battle.result = int(choice)
    db.session.commit()

    return jsonify(prepare_battle(category))


@app.route("/api/get_ranking")
def api_get_ranking():
    category = request.args.get("category", default="any", type=str)
    order = request.args.get("order", default="descending", type=str)
    strokes = request.args.get("strokes", default=False, type=lambda x: x.lower() == "true")

    limit = request.args.get("limit", default=25, type=int)
    if limit < 1:
        limit = 1
    elif limit > 1000:
        limit = 1000
    offset = request.args.get("offset", default=0, type=int)
    if offset < 0:
        offset = 0
    votemin = request.args.get("votemin", default=0, type=int)
    if votemin < 0:
        votemin = 0

    query = Drawing.query
    if category != "any" and category in qd.drawing_names:
        query = query.filter_by(category=category)

    query = query.filter(Drawing.votes >= votemin)

    if order.lower() == "ascending":
        query = query.order_by(Drawing.score)
    else:
        query = query.order_by(Drawing.score.desc())

    count = query.count()

    query = query.limit(limit)
    query = query.offset(offset)

    drawings = query.all()

    output = {
        "count": count,
        "drawings": []
    }
    # TODO: query select fields
    for row in drawings:
        drawing = {
            "key_id": row.key_id,
            "category": row.category,
            "countrycode": row.countrycode,
            "recognized": row.recognized,
            "wins": row.wins,
            "losses": row.losses,
            "score": row.score
        }
        if strokes:
            drawing["strokes"] = json.loads(row.strokes)
        output["drawings"].append(drawing)

    # Use simplejson.dumps, because you can't serialize Decimal objects with json.dumps
    return jsonify(output)


if __name__ == "__main__":
    app.run()
