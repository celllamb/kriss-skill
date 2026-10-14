"""Lossless, source-bound plain-text speaker notes, independent of slide pixels.

The source is data-notes in the settled browser DOM, not PPTX-generated text.
Whitespace and paragraph order are meaningful: never trim or normalize the text.
Error reports expose hashes/counts rather than copying potentially private notes.
"""
from __future__ import annotations

import hashlib
from typing import Any

SCHEMA = 'kriss-speaker-notes-v1'


def source_notes(source: dict[str, Any]) -> str:
    """Read the independently captured notes contract or fail closed."""
    note = source.get('speakerNotes')
    if not isinstance(note, dict) or note.get('schema') != SCHEMA:
        raise ValueError('missing or unsupported speaker-notes source contract')
    if note.get('attributePresent') is not True:
        raise ValueError('final DOM data-notes attribute is absent')
    text = note.get('text')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('final DOM data-notes must contain nonblank plain text')
    return text


def validate_notes_source(source: dict[str, Any]) -> list[dict[str, str]]:
    try:
        source_notes(source)
    except (ValueError, TypeError, AttributeError) as error:
        return [{'code': 'invalid-speaker-notes-source', 'error': str(error)}]
    return []


def notes_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Invalid or stale source evidence never counts as an equal reread."""
    try:
        return source_notes(left) == source_notes(right)
    except (ValueError, TypeError, AttributeError):
        return False


def write_notes(slide: Any, source: dict[str, Any]) -> None:
    text = source_notes(source)
    frame = slide.notes_slide.notes_text_frame
    if frame is None:
        raise ValueError('notes slide has no body placeholder for source notes')
    frame.text = text


def _summary(text: str) -> dict[str, Any]:
    return {'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'characters': len(text)}


def check_native_notes(slide: Any, source: dict[str, Any]) -> dict[str, Any]:
    errors = validate_notes_source(source)
    result: dict[str, Any] = {'pass': False, 'errors': errors}
    if errors:
        return result
    expected = source_notes(source)
    result['expected'] = _summary(expected)
    try:
        # Accessing notes_slide on a slide without notes would create a part.
        # A read-only validator must first check whether it actually exists.
        if not slide.has_notes_slide:
            errors.append({'code': 'missing-native-speaker-notes'})
            return result
        frame = slide.notes_slide.notes_text_frame
        if frame is None:
            errors.append({'code': 'missing-native-notes-body'})
            return result
        actual = frame.text
        result['actual'] = _summary(actual)
        if actual != expected:
            errors.append({'code': 'native-speaker-notes-mismatch',
                           'error': 'notes text/whitespace/order differ from final DOM'})
    except (KeyError, ValueError, AttributeError, TypeError) as error:
        errors.append({'code': 'unreadable-native-speaker-notes', 'error': type(error).__name__})
    result['pass'] = not errors
    return result
