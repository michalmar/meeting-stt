#!/bin/bash
set -e

sudo apt update
# pip install --upgrade pip 
# pip install -r src/requirements.txt

cd ./backend
uv venv
source .venv/bin/activate
uv sync

