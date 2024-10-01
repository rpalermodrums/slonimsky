import asyncio
import os
import time
import platform
import logging
from typing import List

from mingus.containers import Note
from mingus.midi import fluidsynth
from scales import Scale

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_fluidsynth(soundfont_path: str = './soundfonts/Yamaha-C7-Grand-Piano.sf2') -> bool:
    """
    Initializes FluidSynth with the specified soundfont.

    :param soundfont_path: Path to the soundfont file.
    :return: True if initialization is successful, False otherwise.
    """
    try:
        logger.info("Initializing FluidSynth...")
        if not os.path.exists(soundfont_path):
            logger.error(f"Soundfont file not found at {soundfont_path}")
            return False

        os_name = platform.system()
        if os_name == 'Darwin':
            audio_driver = 'coreaudio'
        elif os_name == 'Windows':
            audio_driver = 'dsound'
        else:
            audio_driver = 'alsa'  # Default to ALSA for Linux

        fluidsynth.init(soundfont_path, audio_driver)
        fluidsynth.set_instrument(0, 1)  # Channel 0, program 1 (Acoustic Grand Piano)
        logger.info("FluidSynth initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing FluidSynth: {str(e)}")
        return False

def play_note_sequence(notes: List[str], bpm: int = 120, channel: int = 0) -> None:
    """
    Plays a sequence of notes using FluidSynth.

    :param notes: List of note names (e.g., ['C4', 'E4', 'G4'])
    :param bpm: Tempo in beats per minute.
    :param channel: MIDI channel to play notes on.
    """
    duration = 60 / bpm  # Duration of a quarter note in seconds
    for note in notes:
        try:
            logger.info(f"Playing note: {note}")
            n = Note(note)
            n.velocity = 100
            fluidsynth.play_Note(n, channel)
            time.sleep(duration)
            fluidsynth.stop_Note(n, channel)
        except Exception as e:
            logger.error(f"Error playing note {note}: {e}")

def play_melody_async(melody: List[str], bpm: int = 120, channel: int = 0) -> None:
    """
    Asynchronously plays a melody using FluidSynth.

    :param melody: List of note names.
    :param bpm: Tempo in BPM.
    :param channel: MIDI channel.
    """
    async def _play():
        duration = 60 / bpm
        for note in melody:
            try:
                logger.info(f"Playing note asynchronously: {note}")
                n = Note(note)
                n.velocity = 100
                fluidsynth.play_Note(n, channel)
                await asyncio.sleep(duration)
                fluidsynth.stop_Note(n, channel)
            except Exception as e:
                logger.error(f"Error playing note {note}: {e}")
    asyncio.run(_play())

def play_scale(scale: Scale, bpm: int, channel: int = 0) -> None:
    """
    Plays a given scale at the specified BPM.

    :param scale: Scale instance to play.
    :param bpm: Tempo in beats per minute.
    :param channel: MIDI channel to play notes on.
    """
    duration = 60 / bpm  # Duration of a quarter note in seconds
    for note in scale.notes:
        try:
            logger.info(f"Playing scale note: {note}")
            n = Note(note)
            n.velocity = 100
            fluidsynth.play_Note(n, channel)
            time.sleep(duration)
            fluidsynth.stop_Note(n, channel)
        except Exception as e:
            logger.error(f"Error playing note {note}: {e}")

def play_progression(progression: List[List[str]], bpm: int, channel: int = 0) -> None:
    """
    Plays a chord progression at the specified BPM.

    :param progression: List of chords, each chord is a list of note names.
    :param bpm: Tempo in beats per minute.
    :param channel: MIDI channel to play chords on.
    """
    duration = 60 / bpm  # Duration per chord in seconds
    for chord in progression:
        try:
            logger.info(f"Playing chord progression: {chord}")
            # Play all notes in the chord
            for note in chord:
                n = Note(note)
                n.velocity = 100
                fluidsynth.play_Note(n, channel)
            time.sleep(duration)
            # Stop all notes in the chord
            for note in chord:
                n = Note(note)
                fluidsynth.stop_Note(n, channel)
        except Exception as e:
            logger.error(f"Error playing chord {chord}: {e}")