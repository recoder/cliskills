"""Runtime context objects for skill commands."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SkillContext:
    """Context passed to skill command functions."""

    working_directory: Path = field(default_factory=Path.cwd)
    environment: Mapping[str, str] | None = None
