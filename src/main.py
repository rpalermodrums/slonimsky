import sys
import logging
from argparse import ArgumentParser, Namespace

from mingus.core import scales

from playback import initialize_fluidsynth, play_note_sequence
from models import NoteEvent, ChordEvent, RhythmicPattern, Motif
from graph.integrated_music_graph import IntegratedMusicGraph
from scales import Scale
from melody import MelodyGenerator

def validate_arguments(root_note: str, bpm: int, progression_pattern: list):
    """
    Validates command-line arguments.

    :param root_note: Root note.
    :param bpm: Beats per minute.
    :param progression_pattern: Chord progression pattern.
    :return: None
    :raises ValueError: If any argument is invalid.
    """
    from mingus.core.notes import note_to_int, NoteFormatError

    try:
        note_to_int(root_note.upper())
    except NoteFormatError:
        raise ValueError(f"Invalid root note '{root_note}'. Please enter a valid note (e.g., C, C#, Db, D, etc.).")

    if not (30 < bpm <= 300):
        raise ValueError(f"BPM '{bpm}' is out of valid range (31-300).")

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

    if not args.root_note:
        args.root_note = input('Enter root note (e.g., C, D#, F) [default: C]: ').strip() or 'C'
    if not args.bpm:
        bpm_input = input('Enter BPM (e.g., 120) [default: 120]: ').strip()
        args.bpm = int(bpm_input) if bpm_input.isdigit() else 120
    if not args.progression_pattern:
        progression_input = input('Enter progression pattern (e.g., I IV V) [default: ii V I]: ').strip() or 'ii V I'
        args.progression_pattern = progression_input.split()
    return args

def main():
    """
    Main execution function.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("application.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting the Musical Pattern Generator.")
    
    args = get_user_input()
    
    try:
        validate_arguments(root_note=args.root_note, bpm=args.bpm, progression_pattern=args.progression_pattern)
        logger.info("Validated arguments: Root Note=%s, BPM=%d, Progression=%s", 
                    args.root_note, args.bpm, args.progression_pattern)
    except ValueError as e:
        logger.error("Input validation error: %s", e)
        print(f"Input validation error: {e}")
        sys.exit(1)
    
    if not initialize_fluidsynth():
        logger.warning("FluidSynth initialization failed. Audio playback will be disabled.")
        audio_available = False
    else:
        audio_available = True

    main_scale = Scale(name=f"{args.root_note}_major", mingus_scale_cls=scales.Major, root_note=args.root_note)
    chord_progression = [ChordEvent(symbol=symbol, type='maj7', degrees=[]) for symbol in args.progression_pattern]

    rhythms = [
        RhythmicPattern(pattern='quarter', tempo=args.bpm, accent='strong'),
        RhythmicPattern(pattern='eighth', tempo=args.bpm, accent='weak'),
    ]

    motifs = [
        Motif(name='motif1', contour='ascending', length=4),
        Motif(name='motif2', contour='descending', length=4),
    ]

    integrated_graph_builder = IntegratedMusicGraph()
    scale_notes = []
    for note in main_scale.generate_notes():
        note_event = NoteEvent(
            note=note + '4',
            time=0.0,
            chord='',
            beat_type='neutral',
            consonance='consonant'
        )
        scale_notes.append(note_event)

    integrated_graph_builder.build_full_graph(
        scale_notes=scale_notes,
        chords=chord_progression,
        rhythms=rhythms,
        motifs=motifs
    )
    integrated_graph = integrated_graph_builder.get_integrated_graph()

    melody_gen = MelodyGenerator(integrated_graph)
    try:
        logger.info("Generating melody using Dijkstra's algorithm.")
        melody = melody_gen.generate_melody_dijkstra()
        logger.debug("Generated Melody: %s", melody)
        print(f"Generated Melody: {melody}")
        
        if audio_available:
            logger.info("Playing melody through MIDI.")
            play_note_sequence(melody, bpm=args.bpm)
    except Exception as e:
        logger.exception("Error generating or playing melody.")
        print(f"Error generating or playing melody: {e}")
    
    logger.info("Musical Pattern Generator finished successfully.")
    
if __name__ == "__main__":
    main()
