from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator
import logging

logger = logging.getLogger(__name__)

class NoteEvent(BaseModel):
    note: str
    time: float
    chord: str
    beat_type: Literal['strong', 'weak', 'neutral']
    consonance: Literal['consonant', 'dissonant']

    @field_validator('note')
    def validate_note_format(cls, v):
        import re
        pattern = r'^[A-Ga-g](#|b)?\d+$'
        if not re.match(pattern, v):
            logger.error('Invalid note format: %s. Expected format like "C4", "G#3", etc.', v)
            raise ValueError('Invalid note format. Expected format like "C4", "G#3", etc.')
        logger.debug('Note format validated: %s', v)
        return v

    class Config:
        populate_by_name = True
        str_strip_whitespace = True

class Edge(BaseModel):
    from_node: NoteEvent
    to_node: NoteEvent
    weight: float
    interval: int
    melodic_rules: Dict[str, bool]

    @field_validator('weight')
    def validate_weight(cls, v):
        if not (0 <= v <= 100):
            logger.error('Invalid weight: %s. Weight must be between 0 and 100.', v)
            raise ValueError('Weight must be between 0 and 100.')
        logger.debug('Weight validated: %s', v)
        return v

    @field_validator('interval')
    def validate_interval(cls, v):
        if not (-24 <= v <= 24):
            logger.error('Invalid interval: %s. Interval must be between -24 and 24 semitones.', v)
            raise ValueError('Interval must be between -24 and 24 semitones.')
        logger.debug('Interval validated: %s', v)
        return v

class Transition(BaseModel):
    to_note: str
    chords: List[str]           # Chords in which this transition is valid
    beat_positions: List[str]   # 'strong', 'weak', 'neutral'
    type: Literal['consonant', 'dissonant']  # 'consonant' or 'dissonant'

class ChordEvent(BaseModel):
    symbol: str
    type: str
    degrees: List[int] = Field(default_factory=list)  # Scale degrees

class RhythmicPattern(BaseModel):
    pattern: str
    tempo: int
    accent: str

class Motif(BaseModel):
    name: str
    contour: str
    length: int
    similarity: float = 1.0  # Default similarity score

class RhythmEvent(BaseModel):
    pattern_id: str = Field(..., description="Unique identifier for the rhythm pattern")
    pattern: str = Field(..., description="Rhythmic pattern notation, e.g., 'quarter, quarter, half'")
    tempo: int = Field(..., ge=20, le=300, description="Tempo in beats per minute")

    @field_validator('pattern_id')
    def validate_pattern_id(cls, v):
        if not v:
            logger.error('Invalid pattern_id: %s. pattern_id must be a non-empty string.', v)
            raise ValueError('pattern_id must be a non-empty string.')
        logger.debug('Pattern ID validated: %s', v)
        return v

    @field_validator('pattern')
    def validate_pattern(cls, v):
        if not v:
            logger.error('Invalid pattern: %s. pattern must be a non-empty string.', v)
            raise ValueError('pattern must be a non-empty string.')
        logger.debug('Pattern validated: %s', v)
        # Additional pattern validation can be added here
        return v

    class Config:
        populate_by_name = True
        str_strip_whitespace = True

class TimbreEvent(BaseModel):
    instrument: str = Field(..., description="Name of the instrument, e.g., 'Piano', 'Violin'")
    characteristics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Characteristics of the timbre, such as 'bright': True, 'reverb': 'large'"
    )

    @field_validator('instrument')
    def validate_instrument(cls, v):
        if not v:
            logger.error('Invalid instrument: %s. instrument must be a non-empty string.', v)
            raise ValueError('instrument must be a non-empty string.')
        logger.debug('Instrument validated: %s', v)
        return v

    @field_validator('characteristics')
    def validate_characteristics(cls, v):
        if not isinstance(v, dict):
            logger.error('Invalid characteristics: %s. characteristics must be a dictionary.', v)
            raise ValueError('characteristics must be a dictionary.')
        logger.debug('Characteristics validated: %s', v)
        # Additional validation for characteristics can be added here
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        str_strip_whitespace = True

class OtherEvent(BaseModel):
    identifier: str = Field(..., description="Unique identifier for the event")
    description: str = Field(..., description="Description of the event")

    @field_validator('identifier')
    def validate_identifier(cls, v):
        if not v:
            logger.error('Invalid identifier: %s. identifier must be a non-empty string.', v)
            raise ValueError('identifier must be a non-empty string.')
        logger.debug('Identifier validated: %s', v)
        return v

    @field_validator('description')
    def validate_description(cls, v):
        if not v:
            logger.error('Invalid description: %s. description must be a non-empty string.', v)
            raise ValueError('description must be a non-empty string.')
        logger.debug('Description validated: %s', v)
        return v

    class Config:
        populate_by_name = True
        str_strip_whitespace = True
