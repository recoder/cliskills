"""Manifest generation helpers."""

from .models import SkillCapabilities, SkillCommand, SkillManifest


def create_manifest(
    *,
    name: str,
    version: str,
    description: str,
    commands: list[SkillCommand] | None = None,
    capabilities: SkillCapabilities | None = None,
) -> SkillManifest:
    """Create a skill manifest with stable defaults."""
    return SkillManifest(
        name=name,
        version=version,
        description=description,
        commands=commands or [],
        capabilities=capabilities or SkillCapabilities(),
    )
