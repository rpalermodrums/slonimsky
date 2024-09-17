import sys
from argparse import ArgumentParser, Namespace

from mingus.core import scales

from playback import initialize_fluidsynth, play_note_sequence
from models import NoteEvent, Edge
from graph import ScaleGraph
from scales import Scale
from melody import MelodyGenerator

def validate_arguments(**kwargs):
    """
    Validates command-line arguments.

    :param args: Parsed arguments.
    :return: None
    :raises ValueError: If any argument is invalid.
    """
    from mingus.core.notes import note_to_int, NoteFormatError

    try:
        # Validate root note
        note_to_int(kwargs['root_note'].upper())
    except NoteFormatError:
        raise ValueError(f"Invalid root note '{kwargs['root_note']}'. Please enter a valid note (e.g., C, C#, Db, D, etc.).")

    if not (30 < kwargs['bpm'] <= 300):
        raise ValueError(f"BPM '{kwargs['bpm']}' is out of valid range (31-300).")

def get_user_input() -> Namespace:
    """
    Parses and returns user input from command-line arguments, prompting for any missing arguments.

    :return: Namespace with argument values.
    """
    parser = ArgumentParser(description='Musical Pattern Generator')
    parser.add_argument('--root_note', type=str, help='Root note for scales and chords')
    parser.add_argument('--bpm', type=int, help='Tempo in beats per minute')
    parser.add_argument('--progression_pattern', nargs='+', help='Chord progression pattern (e.g., I IV V)')

    args = parser.parse_args()

    # Prompt for missing arguments with defaults
    if not args.root_note:
        args.root_note = input('Enter root note (e.g., C, D#, F) [default: C]: ').strip() or 'C'
    if not args.bpm:
        args.bpm = int(input('Enter BPM (e.g., 120) [default: 120]: ').strip() or 120)
    if not args.progression_pattern:
        progression_input = input('Enter progression pattern (e.g., I IV V) [default: ii V I]: ').strip() or 'ii V I'
        args.progression_pattern = progression_input.split()
    return args

def main():
    """
    Main execution function.
    """
    args = get_user_input()

    # Validate inputs
    try:
        validate_arguments(root_note=args.root_note, bpm=args.bpm, progression_pattern=args.progression_pattern)
    except ValueError as e:
        print(f"Input validation error: {e}")
        sys.exit(1)

    # Initialize FluidSynth
    if not initialize_fluidsynth():
        print("FluidSynth initialization failed. Audio playback will be disabled.")

    # Initialize Scale and Graph
    main_scale = Scale(name=f"{args.root_note}_major", mingus_scale_cls=scales.Major, root_note=args.root_note)
    chord_progression = [(symbol, 4) for symbol in args.progression_pattern]  # Assuming 4 beats per chord

    scale_graph = ScaleGraph(scale=main_scale, chord_progression=chord_progression, time_signature=(4, 4))
    scale_graph.build_graph()

    # Generate Melody
    melody_gen = MelodyGenerator(scale_graph.graph)
    try:
        melody = melody_gen.generate_melody_dijkstra()
        print(f"Generated Melody: {melody}")
        play_note_sequence(melody, bpm=args.bpm)
    except Exception as e:
        print(f"Error generating or playing melody: {e}")

if __name__ == "__main__":
    main()