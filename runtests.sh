#!/bin/sh
if [ "$LINT" ]; then
    flake8 natural_keys tests --exclude migrations
else
    python setup.py test
fi
