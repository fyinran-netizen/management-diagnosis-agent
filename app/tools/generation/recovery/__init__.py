"""Programmatic, semantics-preserving recovery for structured generation."""

from app.tools.generation.recovery.json_section import (
    DuplicateJSONKeyError,
    RecoveryResult,
    recover_section_json,
    loads_rejecting_duplicate_keys,
)

__all__ = [
    "DuplicateJSONKeyError",
    "RecoveryResult",
    "loads_rejecting_duplicate_keys",
    "recover_section_json",
]
