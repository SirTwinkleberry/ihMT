#!/bin/bash

set -e

export PYTHONPATH=$PYTHONPATH:$(dirname -- "$( readlink -f -- "$0"; )")

python -m coverage run -m unittest

python -m coverage html

python -m coverage report
