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

5. **Run the Application**

   ```bash
   python slonimsky.py
   ```

   You can also provide command-line arguments:
   ```bash
   python slonimsky.py --root_note C --bpm 120 --progression_pattern I IV V
   ```

Remember to deactivate the virtual environment when you're done:



## Contributing
Contributions are welcome! Whether you're reporting bugs, suggesting features, or submitting pull requests, your input helps improve Slonimsky's Thesaurus.

1. **Fork the Repository**

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add a meaningful message about your feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**

Please ensure your code adheres to the project's coding standards and includes appropriate tests where necessary.

## License
This project is licensed under the [MIT License](LICENSE.md). See the [LICENSE](LICENSE.md) file for details.

## Acknowledgements
- **Nicolas Slonimsky**: For his extensive work on scales and melodic patterns that inspired this project.
- **Charles Mingus**: The Mingus library is inspired by the legendary jazz musician.
- **Mingus Python Library**: Providing robust tools for handling musical operations in Python.
- **FluidSynth**: For enabling real-time synthesis of MIDI notes.
- **Open Source Contributors**: Special thanks to all contributors who have helped shape this project.
