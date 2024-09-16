# Slonimsky's Thesaurus: Musical Pattern Generator

## Introduction
This project adapts Nicolas Slonimsky's musical theories for digital application, drawing from his influence on musicians such as John Coltrane and Frank Zappa.

## Overview
The application generates musical patterns based on Slonimsky's "Thesaurus of Scales and Melodic Patterns," using algorithmic interpretations. It utilizes the Mingus library for musical operations.

## Features
* Generate Slonimsky-inspired musical patterns
* Visualize patterns on a piano roll
* Export patterns as MIDI files
* GUI for pattern customization

## Prerequisites

Ensure you have the following prerequisites:

1. **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/).

2. **FluidSynth**: Required for audio playback.

   macOS (Homebrew):
   ```bash
   brew install fluid-synth
   ```

   Ubuntu/Debian:
   ```bash
   sudo apt-get install fluidsynth
   ```

   Windows: Download from [FluidSynth releases](https://github.com/FluidSynth/fluidsynth/releases).

3. **Soundfont**: Download from [FluidSynth SoundFont](https://github.com/FluidSynth/fluidsynth/wiki/SoundFont). Place in a `soundfonts` directory in the project root.

4. **Tkinter**: Included with Python, but may require separate installation on some Linux distributions:

   ```bash
   sudo apt-get install python3-tk
   ```

5. **MIDI support**: For Linux, install additional MIDI support:

   ```bash
   sudo apt-get install libasound2-dev libjack-dev
   ```

## Installation and Setup

Follow these steps to set up a virtual environment:

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/slonimsky-thesaurus.git
   cd slonimsky-thesaurus
   ```

2. **Create a Virtual Environment**

   macOS/Linux:
   ```bash
   python3 -m venv venv
   ```
   Windows:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**

   macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   Windows:
   ```bash
   .\venv\Scripts\activate
   ```

4. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Install python-rtmidi**

   ```bash
   pip install --only-binary=:all: python-rtmidi
   ```

6. **Run the Application**

   ```bash
   python gui.py
   ```

   Or with command-line arguments:
   ```bash
   python slonimsky.py --root_note C --bpm 120 --progression_pattern I IV V
   ```
Remember to deactivate your virtual environment when finished:

```bash
deactivate
```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
