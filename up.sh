#!/usr/bin/env bash

set -euo pipefail

main() {
    export FLASK_APP=scoreboard.py
    echo 'Ensure you activate your virtual environment!'
    docker run \
        -d \
        -p 6379:6379 \
        --rm \
        --name scoreboard-db \
        redis:5.0.2-alpine

    flask run --host=0.0.0.0
}

main
