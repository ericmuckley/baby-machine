#!/bin/bash

# Parent directory (persists, contains venv)
PARENT_DIR=~/baby-machine

# Repo subdirectory (gets deleted and re-cloned)
REPO_DIR="$PARENT_DIR/repo"

# Create parent directory if it doesn't exist
mkdir -p "$PARENT_DIR"

# Remove existing repo directory if it exists
if [ -d "$REPO_DIR" ]; then
    echo "Removing existing repo..."
    rm -rf "$REPO_DIR"
fi

# Clone the repository
echo "Cloning repository..."
git clone https://github.com/ericmuckley/baby-machine.git "$REPO_DIR"

# Create venv if it doesn't exist
if [ ! -d "$PARENT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv --system-site-packages "$PARENT_DIR/venv"
    source "$PARENT_DIR/venv/bin/activate"
    pip install --upgrade pip setuptools wheel
    pip install flask
else
    source "$PARENT_DIR/venv/bin/activate"
fi

# Navigate to the repo and run the app
cd "$REPO_DIR"
echo "Starting the app..."
python -m app