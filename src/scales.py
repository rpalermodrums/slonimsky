from typing import List, Optional
from mingus.core import scales as mingus_scales, intervals
from mingus.core import notes
import logging

logger = logging.getLogger(__name__)

class Scale:
    def __init__(self, name: str, mingus_scale_cls = None, root_note: str = 'C', notes: Optional[List[str]] = None):
        """
        Initializes a Scale with a name, Mingus scale class, and root note.

        :param name: Name of the scale
        :param mingus_scale_cls: Mingus Scale subclass (e.g., scales.Major)
        :param root_note: Root note of the scale
        :param notes: Optional list of notes (overrides Mingus scale)
        """
        self.name = name
        self.root_note = root_note
        self.mingus_scale_cls = mingus_scale_cls

        if notes is not None:
            self.notes = notes
            logger.debug(f"Initialized scale '{self.name}' with provided notes: {self.notes}")
        elif mingus_scale_cls is not None:
            self.mingus_scale = mingus_scale_cls(self.root_note)
            self.notes = self.generate_notes()
            logger.debug(f"Initialized scale '{self.name}' using Mingus scale class: {mingus_scale_cls.__name__}")
        else:
            self.notes = []
            logger.warning(f"Initialized scale '{self.name}' with no notes provided.")

    def generate_notes(self) -> List[str]:
        """
        Generates the notes of the scale.

        :return: List of note names.
        """
        notes = self.mingus_scale.ascending()
        logger.debug(f"Generated notes for scale '{self.name}': {notes}")
        return notes

    def rotate(self, steps: int = 1) -> 'Scale':
        """
        Rotates the scale by a number of steps.

        :param steps: Number of steps to rotate.
        :return: New Scale instance with rotated notes.
        """
        rotated_notes = self.notes[steps:] + self.notes[:steps]
        rotated_name = f"{self.name}_rotated_{steps}"
        logger.info(f"Rotated scale '{self.name}' by {steps} steps to create '{rotated_name}'")
        return Scale(rotated_name, self.mingus_scale_cls, self.root_note, notes=rotated_notes)

    def invert(self) -> 'Scale':
        """
        Inverts the scale by reflecting its intervals around the tonic.

        :return: New Scale instance with inverted notes.
        """
        inverted_intervals = self._invert_intervals()
        inverted_notes = [self.root_note]
        current_note = self.root_note

        for interval in inverted_intervals:
            try:
                current_note_int = notes.note_to_int(current_note)
                next_note_int = (current_note_int + interval) % 12
                next_note = notes.int_to_note(next_note_int)
                inverted_notes.append(next_note)
                current_note = next_note
            except Exception as e:
                logger.error(f"Error inverting scale '{self.name}': {e}")
                break

        inverted_name = f"{self.name}_inverted"
        logger.info(f"Inverted scale '{self.name}' to create '{inverted_name}'")
        return Scale(inverted_name, None, self.root_note, notes=inverted_notes)

    def _invert_intervals(self) -> List[int]:
        """
        Inverts the intervals of the scale around the tonic.

        :return: List of inverted intervals in semitones.
        """
        ascending_notes = self.notes  # Use the current notes
        intervals_list = []
        for i in range(1, len(ascending_notes)):
            interval = intervals.measure(ascending_notes[i - 1], ascending_notes[i])
            intervals_list.append(interval)

        # Invert intervals: each interval becomes its complement to 12
        inverted_intervals = [(12 - interval) % 12 for interval in intervals_list]
        logger.debug(f"Inverted intervals for scale '{self.name}': {inverted_intervals}")
        return inverted_intervals

    def __str__(self) -> str:
        return f"Scale: {self.name}, Notes: {self.notes}"

    def get_primary_notes(self) -> List[str]:
        """
        Retrieves the primary notes of the scale, typically within a specific octave.

        :return: List of primary note names.
        """
        logger.debug(f"Retrieving primary notes for scale '{self.name}': {self.notes}")
        return self.notes

class ScaleGenerator:
    def __init__(self):
        """
        Initializes the ScaleGenerator with a list of available Mingus scale classes.
        """
        self.available_scale_classes = [
            mingus_scales.Aeolian,
            mingus_scales.Bachian,
            mingus_scales.Chromatic,
            mingus_scales.Dorian,
            mingus_scales.HarmonicMajor,
            mingus_scales.HarmonicMinor,
            mingus_scales.Ionian,
            mingus_scales.Locrian,
            mingus_scales.Lydian,
            mingus_scales.Major,
            mingus_scales.MelodicMinor,
            mingus_scales.MinorNeapolitan,
            mingus_scales.Mixolydian,
            mingus_scales.NaturalMinor,
            mingus_scales.Octatonic,
            mingus_scales.Phrygian,
            mingus_scales.WholeTone
        ]
        self.scales: List[Scale] = []
        logger.info("Initialized ScaleGenerator with available scale classes.")

    def generate_custom_scales(self, root_note: str) -> None:
        """
        Generates scales based on the specified root note.

        :param root_note: Root note for the scales.
        """
        self.scales.clear()
        logger.info(f"Generating custom scales for root note '{root_note}'")
        for scale_cls in self.available_scale_classes:
            try:
                scale_name = f"{root_note}_{scale_cls.__name__}"
                scale = Scale(name=scale_name, mingus_scale_cls=scale_cls, root_note=root_note)
                self.scales.append(scale)
                logger.debug(f"Generated scale '{scale_name}'")
            except Exception as e:
                logger.error(f"Error generating scale {scale_cls.__name__} for root note {root_note}: {e}")

    def catalog_scales(self, root_note: str) -> None:
        """
        Generates additional patterns (rotations and inversions) for each scale.

        :param root_note: Root note used for generating scales.
        """
        logger.info(f"Cataloging scales for root note '{root_note}'")
        for scale in self.scales.copy():
            # Generate all possible rotations for the scale
            for steps in range(1, len(scale.notes)):
                rotated_scale = scale.rotate(steps)
                self.scales.append(rotated_scale)

            # Generate inversion of the scale
            inverted_scale = scale.invert()
            self.scales.append(inverted_scale)

    def get_all_scales(self) -> List[Scale]:
        """
        Retrieves all generated scales.

        :return: List of Scale instances.
        """
        logger.debug(f"Retrieving all generated scales: {self.scales}")
        return self.scales
    
    def generate_scale(self, root_note: str) -> None:
        """
        Generates and catalogs scales for a given root note.

        :param root_note: The root note for which to generate scales.
        """
        logger.info(f"Generating and cataloging scales for root note '{root_note}'")
        self.generate_custom_scales(root_note)
        self.catalog_scales(root_note)