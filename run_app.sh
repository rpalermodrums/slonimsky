#!/bin/bash

# Function to check if we're in a virtual environment
in_venv() {
    [ -n "$VIRTUAL_ENV" ]
}

# Function to create and activate a virtual environment
create_and_activate_venv() {
    echo "Creating a new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
}

# Check if we're already in a virtual environment
if ! in_venv; then
    # Check if a 'venv' directory exists
    if [ -d "venv" ]; then
        echo "Activating existing virtual environment..."
        source venv/bin/activate
    else
        create_and_activate_venv
    fi
else
    echo "Already in a virtual environment."
fi

# Ensure pip is up to date
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install python-rtmidi
pip install --only-binary=:all: python-rtmidi==1.5.3

# Run the GUI application
python gui.py

# Deactivate the virtual environment if we activated it
if [ -z "$VIRTUAL_ENV" ]; then
    deactivate
fi