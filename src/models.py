from typing import Literal, Dict
from pydantic import BaseModel, field_validator

class NoteEvent(BaseModel):
    note: str
    time: float
    chord: str
    beat_type: Literal['strong', 'weak']
    consonance: Literal['consonant', 'dissonant']

    @field_validator('note')
    def validate_note_format(cls, v):
        import re
        pattern = r'^[A-Ga-g](#|b)?\d$'
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

    @field_validator('weight')
    def validate_weight(cls, v):
        if not (0 <= v <= 100):
            raise ValueError('Weight must be between 0 and 100.')
        return v

    @field_validator('interval')
    def validate_interval(cls, v):
        if not (-24 <= v <= 24):
            raise ValueError('Interval must be between -24 and 24 semitones.')
        return v