import os
import random
import uuid
import datetime
from flask import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, case
from quickdraw import QuickDrawData

CACHE_DIR = "../quickdraw_dataset_bin"

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
app.secret_key = os.urandom(32)

db = SQLAlchemy(app)
qd = QuickDrawData(cache_dir=CACHE_DIR, print_messages=False)


def uuid_gen() -> str:
    return str(uuid.uuid4()).replace("-", "")


# https://www.evanmiller.org/how-not-to-sort-by-average-rating.html
def ci_lower_bound(pos: int, neg: int):
    n = pos + neg
    z = 1.96  # 0.975
    return case(
        [(n == 0, 0)],
        else_=((pos + z**2/2) / n - z * func.sqrt((pos * neg) / n + z**2/4) / n) / (1 + z**2 / n)
    )


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
    score = db.column_property(ci_lower_bound(wins, losses))


class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(32), default=uuid_gen)
    ip = db.Column(db.String)
    datetime = db.Column(db.DateTime, default=datetime.datetime.now)
    category = db.Column(db.String)
    drawing1 = db.Column(db.String(16))
    drawing2 = db.Column(db.String(16))
    result = db.Column(db.Integer, default=0)


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


def new_battle(category: str) -> dict:
    if category == "any" or category not in qd.drawing_names:
        category = random.choice(qd.drawing_names)

    # Pick 2 drawings
    drawings = []

    for _ in range(2):
        drawing = None
        # 80% chance for old drawing, 20% chance for new drawing
        if random.random() > 0.2:
            drawing = Drawing.query.filter_by(category=category).order_by(func.random()).first()
            # If other drawing has same ID, get new drawing instead
            for other_drawing in drawings:
                if drawing.key_id == other_drawing.key_id:
                    drawing = None
                    break
        if not drawing:
            while True:
                qd_drawing = qd.get_drawing(category)
                drawing = Drawing.query.filter_by(key_id=str(qd_drawing.key_id)).first()
                if not drawing:
                    drawing = Drawing(
                        key_id=str(qd_drawing.key_id),
                        category=category,
                        countrycode=qd_drawing.countrycode,
                        recognized=qd_drawing.recognized,
                        strokes=json.dumps(qd_drawing.strokes, separators=(',', ':'))
                    )
                    db.session.add(drawing)

                # If other drawing as same ID, get new drawing again
                for other_drawing in drawings:
                    if drawing.key_id == other_drawing.key_id:
                        continue
                break

        drawings.append(drawing)

    db.session.commit()

    battle = Battle(
        ip=request.remote_addr,
        category=category,
        drawing1=drawings[0].key_id,
        drawing2=drawings[1].key_id
    )

    db.session.add(battle)
    db.session.commit()

    return {
        "success": True,
        "id": battle.uuid,
        "category": category,
        "strokes1": json.loads(drawings[0].strokes),
        "strokes2": json.loads(drawings[1].strokes)
    }


@app.route("/api/new_battle")
def api_new_battle():
    category = request.args.get("category", default="any", type=str)
    return jsonify(new_battle(category))


@app.route("/api/vote")
def api_vote():
    choice = request.args.get("choice", default="0", type=str)
    uuid = request.args.get("battle", default="1337", type=str)
    category = request.args.get("category", default="any", type=str)

    if choice not in ("1", "2"):
        return jsonify(success=False, reason="Not a valid choice")

    battle = Battle.query.filter_by(uuid=uuid).first()
    if not battle:
        return jsonify(success=False, reason="Not a valid battle")

    if battle.result != 0:
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

    return jsonify(new_battle(category))


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
    return jsonify(output)


if __name__ == "__main__":
    app.run()
