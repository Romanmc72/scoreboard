#!/usr/bin/env python3
"""
This is the scoreboard tracking app. An API that can be hit and updated to
reflect the score for everyone to view.
"""
import json
import os

from flask import Flask
from flask import abort
from flask import request
from flask import render_template
from flask import Response
import redis

app = Flask(__name__)
db = redis.Redis()


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


@app.route('/', methods=['GET'])
def index():
    """This is the actual scoreboard display"""
    return render_template("base.html")


@app.route('/api/score/<name>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def api_user(name):
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
        score = db.get(name)
        if score is None:
            return Response(json.dumps({'error': f'score not found for `{name}`'}), mimetype='application/json', status=404)
        return Response(json.dumps({'name': name, 'score': score}), mimetype='application/json', status=200)

    elif request.method == 'DELETE':
        unlinked = db.unlink(name)
        return Response(json.dumps({'name': name, 'action': 'delete' if unlinked != 0 else 'pass'}), mimetype='application/json', status=200)

    elif request.method == 'PUT':
        method = data.get('method', 'replace')
        try:
            score = int(data.get('score', 0))
        except ValueError:
            return Response(json.dumps({'error': f'invalid score entry `{score}`, use integer.'}), mimetype='application/json', status=400)

        current_score = db.get(name)
        no_score = current_score is None
        if no_score or method == 'replace':
            db.set(name, score)
            return Response(json.dumps({'name': name, 'score': score}), mimetype='application/json', status=200)
        else:
            current_score = int(current_score.decode('utf-8'))

        if method == 'add':
            current_score += score
        else:
            return Response(json.dumps({'error': f'invalid method `{method}`, use one of <add|subtract|replace>'}), mimetype='application/json', status=400)

        db.set(name, current_score)
        return Response(json.dumps({'name': name, 'score': current_score}), mimetype='application/json', status=200)

    elif request.method == 'POST':
        try:
            score = int(data.get('score', 0))
        except ValueError:
            return Response(json.dumps({'error': f'invalid score entry `{score}`, use integer.'}), mimetype='application/json', status=400)
        if db.get(name) is None:
            db.set(name, score)
            return Response(json.dumps({'name': name, 'score': score}), mimetype='application/json', status=200)
        else:
            return Response(json.dumps({'error': f'`{name}` already exists'}), mimetype='application/json', status=400)


@app.route('/api/scoreboard', methods=['GET', 'DELETE', 'PUT'])
def api_scoreboard():
    """Get the scoreboard! Or clear it."""
    if request.method == 'GET':
        return Response(json.dumps(get_all_of_the_things()), mimetype='application/json', status=200)
    elif request.method == 'DELETE':
        return Response(json.dumps(delete_all_of_the_things()), mimetype='application/json', status=200)
    elif request.method == 'PUT':
        return Response(json.dumps(clear_all_of_the_things()), mimetype='application/json', status=200)


def get_all_of_the_things():
    """Get everything from the redis db"""
    the_things = list()
    for key in db.keys():
        plain_key = key.decode('utf-8')
        plain_value = db.get(key).decode('utf-8')
        the_things.append({
            "name": plain_key,
            "score": int(plain_value)
        })
    the_things = sorted(the_things, key=lambda x: x['score'], reverse=True)
    return the_things


def delete_all_of_the_things():
    """Get everything from the redis db"""
    for key in db.keys():
        db.unlink(key)
    return get_all_of_the_things()


def clear_all_of_the_things():
    for key in db.keys():
        db.set(key, 0)
    return get_all_of_the_things()


if __name__ == "__main__":
    app.run()
