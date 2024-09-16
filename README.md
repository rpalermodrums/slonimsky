# Slonimsky's Thesaurus: Musical Pattern Generator

## Introduction
Inspired by Nicolas Slonimsky's groundbreaking work and its profound influence on musicians from John Coltrane to Frank Zappa, this project brings Slonimsky's musical theories into the digital age.

## Overview
This application generates musical patterns based on Slonimsky's "Thesaurus of Scales and Melodic Patterns," using algorithmic interpretations of his theories. It leverages the Mingus library, itself inspired by the legendary Charles Mingus, to handle musical operations.

## Features
* Generate Slonimsky-inspired musical patterns
* Visualize patterns on a piano roll
* Export patterns as MIDI files
* User-friendly GUI for easy pattern customization

## Prerequisites

Before installing the application, ensure you have the following prerequisites:

1. **Python 3.8+**: This project requires Python 3.8 or higher. You can download it from [python.org](https://www.python.org/downloads/).

2. **FluidSynth**: This is required for audio playback.

   On macOS (using Homebrew):
   ```bash
   brew install fluid-synth
   ```

   On Ubuntu or Debian:
   ```bash
   sudo apt-get install fluidsynth
   ```

   On Windows, you can download FluidSynth from [here](https://github.com/FluidSynth/fluidsynth/releases).

3. **Soundfont**: FluidSynth requires a soundfont file. You can download one from [here](https://github.com/FluidSynth/fluidsynth/wiki/SoundFont). Place it in a `soundfonts` directory in your project root.

4. **Tkinter**: This is usually included with Python, but on some Linux distributions, you might need to install it separately:

   ```bash
   sudo apt-get install python3-tk
   ```

5. **MIDI support**: On Linux, you might need to install additional MIDI support:

   ```bash
   sudo apt-get install libasound2-dev libjack-dev
   ```

## Installation and Setup

To run the Slonimsky's Thesaurus application, follow these steps to set up a virtual environment:

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/slonimsky-thesaurus.git
   cd slonimsky-thesaurus
   ```

2. **Create a Virtual Environment**

   On macOS and Linux:
   ```bash
   python3 -m venv venv
   ```
   On Windows:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**

   On macOS and Linux:
   ```bash
   source venv/bin/activate
   ```
   On Windows:
   ```bash
   .\venv\Scripts\activate
   ```

4. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Install python-rtmidi**

   This package might require special handling:

   ```bash
   pip install --only-binary=:all: python-rtmidi
   ```

6. **Run the Application**

   ```bash
   python gui.py
   ```

   You can also provide command-line arguments:
   ```bash
   python slonimsky.py --root_note C --bpm 120 --progression_pattern I IV V
   ```

Remember to deactivate the virtual environment when you're done:
