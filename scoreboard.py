#!/usr/bin/env python3
"""
This is the scoreboard tracking app. An API that can be hit and updated to
reflect the score for everyone to view.
"""
import json
import re
import os

from flask import Flask
from flask import abort
from flask import redirect
from flask import request
from flask import render_template
from flask import Response
from flask import url_for

from flask_wtf import FlaskForm

from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import Length
from wtforms.validators import Regexp

import redis

app = Flask(__name__)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


GAME_CODE_MATCH = r"^[a-z\-]+$"

class GameCodeForm(FlaskForm):
    """The form for starting a new scoreboard"""
    class Meta:
        csrf = False
    game_code = StringField(
        'Game Code',
        validators=[
            Length(min=4, max=12, message="Please enter a game code between 4 and 12 characters."),
            Regexp(GAME_CODE_MATCH, message="Only use lowercase letters and hyphens.")
        ]
    )
    submit = SubmitField('Join Scoreboard')


@app.shell_context_processor
def make_shell_context():
    """
    Description
    -----------
    flask can run an interactive shell that will
    pre-import anything specified in this function
    under the alias provided for easy python
    interpreter testing without having to retype
    the same import statements every time.

    Call this by running

    $ `flask shell`

    Params
    ------
    None

    Return
    ------
    None
    """
    return {'db': db}


@app.route('/', methods=['GET', 'POST'])
def index():
    """This is the actual scoreboard display"""
    form = GameCodeForm()

    if form.validate_on_submit():
        return redirect(url_for('my_game', game_code=form.game_code.data))
        # return render_template('game.html', game_code=form.game_code.data)

    return render_template("base.html", form=form)


@app.route('/<game_code>', methods=['GET'])
def my_game(game_code):
    """This is the actual scoreboard display"""
    if re.match(GAME_CODE_MATCH, game_code) is None:
        return redirect(url_for('index'))
    else:
        return render_template("game.html", game_code=game_code)


@app.route('/api/scoreboard/<game_code>/score/<name>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def api_user(game_code, name):
    """
    Manipulate a users score with this endpoint.

    Use GET to see the score, but you must pass in the name in the url:

    Use POST to add a new player. This will fail if they exist already.
        {'score': <number>}

    Use PUT to modify an existing player's score.
        {'score': <number>, 'method': '<add|replace>'}
        (default method is 'replace' if omitted)

    Use DELETE to delete a player from the scoreboard.
    """
    data = request.json
    if name is None:
        return Response(json.dumps({'error': 'name not provided'}), mimetype='application/json', status=400)

    if request.method == 'GET':
        score = db.get(game_code + ":" + name)
        if score is None:
            return Response(json.dumps({'error': f'score not found for `{name}`'}), mimetype='application/json', status=404)
        return Response(json.dumps({'name': name, 'score': score}), mimetype='application/json', status=200)

    elif request.method == 'DELETE':
        unlinked = db.unlink(game_code + ":" + name)
        return Response(json.dumps({'name': name, 'action': 'delete' if unlinked != 0 else 'pass'}), mimetype='application/json', status=200)

    elif request.method == 'PUT':
        method = data.get('method', 'replace')
        try:
            score = int(data.get('score', 0))
        except ValueError:
            score = data.get('score')
            return Response(json.dumps({'error': f'invalid score entry `{score}`, use integer.'}), mimetype='application/json', status=400)

        current_score = db.get(game_code + ":" + name)
        no_score = current_score is None
        if no_score or method == 'replace':
            db.set(game_code + ":" + name, score)
            return Response(json.dumps({'name': name, 'score': score}), mimetype='application/json', status=200)
        else:
            current_score = int(current_score.decode('utf-8'))

        if method == 'add':
            current_score += score
        else:
            return Response(json.dumps({'error': f'invalid method `{method}`, use one of <add|subtract|replace>'}), mimetype='application/json', status=400)

        db.set(game_code + ":" + name, current_score)
        return Response(json.dumps({'name': name, 'score': current_score}), mimetype='application/json', status=200)

    elif request.method == 'POST':
        try:
            score = int(data.get('score', 0))
        except ValueError:
            score = data.get('score')
            return Response(json.dumps({'error': f'invalid score entry `{score}`, use integer.'}), mimetype='application/json', status=400)
        if db.get(game_code + ":" + name) is None:
            db.set(game_code + ":" + name, score)
            return Response(json.dumps({'name': name, 'score': score}), mimetype='application/json', status=200)
        else:
            return Response(json.dumps({'error': f'`{name}` already exists'}), mimetype='application/json', status=400)


@app.route('/api/scoreboard/<game_code>', methods=['GET', 'DELETE', 'PUT'])
def api_scoreboard(game_code):
    """Get the scoreboard! Or clear it."""
    if request.method == 'GET':
        return Response(json.dumps(get_all_of_the_things(game_code)), mimetype='application/json', status=200)
    elif request.method == 'DELETE':
        return Response(json.dumps(delete_all_of_the_things(game_code)), mimetype='application/json', status=200)
    elif request.method == 'PUT':
        return Response(json.dumps(clear_all_of_the_things(game_code)), mimetype='application/json', status=200)


def get_all_of_the_things(match_prefix: str = ''):
    """Get everything from the redis db"""
    the_things = list()
    for key in db.keys(pattern=f"{match_prefix}:*"):
        plain_key = key.decode('utf-8')
        plain_value = db.get(key).decode('utf-8')
        game_specific_key = ''.join(plain_key.split(':')[1::])
        the_things.append({
            "name": game_specific_key,
            "score": int(plain_value)
        })
    the_things = sorted(the_things, key=lambda x: x['score'], reverse=True)
    return the_things


def delete_all_of_the_things(match_prefix: str = ''):
    """Get everything from the redis db"""
    for key in db.keys(pattern=f"{match_prefix}:*"):
        db.unlink(key)
    return get_all_of_the_things()


def clear_all_of_the_things(match_prefix: str = ''):
    for key in db.keys(pattern=f"{match_prefix}:*"):
        db.set(key, 0)
    return get_all_of_the_things()


if __name__ == "__main__":
    app.run()
