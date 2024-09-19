from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field, validator

class NoteEvent(BaseModel):
    note: str
    time: float
    chord: str
    beat_type: Literal['strong', 'weak', 'neutral']
    consonance: Literal['consonant', 'dissonant']

    @validator('note')
    def validate_note_format(cls, v):
        import re
        pattern = r'^[A-Ga-g](#|b)?\d+$'
        if not re.match(pattern, v):
            raise ValueError('Invalid note format. Expected format like "C4", "G#3", etc.')
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

    @validator('weight')
    def validate_weight(cls, v):
        if not (0 <= v <= 100):
            raise ValueError('Weight must be between 0 and 100.')
        return v

    @validator('interval')
    def validate_interval(cls, v):
        if not (-24 <= v <= 24):
            raise ValueError('Interval must be between -24 and 24 semitones.')
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

    @validator('pattern_id')
    def validate_pattern_id(cls, v):
        if not v:
            raise ValueError('pattern_id must be a non-empty string.')
        return v

    @validator('pattern')
    def validate_pattern(cls, v):
        if not v:
            raise ValueError('pattern must be a non-empty string.')
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

    @validator('instrument')
    def validate_instrument(cls, v):
        if not v:
            raise ValueError('instrument must be a non-empty string.')
        return v

    @validator('characteristics')
    def validate_characteristics(cls, v):
        if not isinstance(v, dict):
            raise ValueError('characteristics must be a dictionary.')
        # Additional validation for characteristics can be added here
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        str_strip_whitespace = True

class OtherEvent(BaseModel):
    identifier: str = Field(..., description="Unique identifier for the event")
    description: str = Field(..., description="Description of the event")

    @validator('identifier')
    def validate_identifier(cls, v):
        if not v:
            raise ValueError('identifier must be a non-empty string.')
        return v

    @validator('description')
    def validate_description(cls, v):
        if not v:
            raise ValueError('description must be a non-empty string.')
        return v

    class Config:
        populate_by_name = True
        str_strip_whitespace = True
