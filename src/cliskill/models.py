"""Core contract models."""

from typing import Any, Literal

from pydantic import BaseModel, Field

OutputFormat = Literal["json", "markdown", "toon"]


def default_output_formats() -> list[OutputFormat]:
    """Return default machine-readable output formats."""
    return ["json", "markdown", "toon"]


class SkillCapabilities(BaseModel):
    """Declared side-effect capabilities for a skill or command."""

    filesystem_read: bool = False
    filesystem_write: bool = False
    file_deletion: bool = False
    network_access: bool = False
    secret_access: bool = False
    subprocess_execution: bool = False
    destructive_operations: bool = False
    generated_artifacts: bool = False


class SkillCommand(BaseModel):
    """Manifest entry for one skill command."""

    name: str
    description: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    formats: list[OutputFormat] = Field(default_factory=default_output_formats)
    capabilities: SkillCapabilities = Field(default_factory=SkillCapabilities)


class SkillManifest(BaseModel):
    """Machine-readable description of a CLI skill."""

    contract_version: str = "0.1"
    name: str
    version: str
    description: str
    commands: list[SkillCommand] = Field(default_factory=list)
    capabilities: SkillCapabilities = Field(default_factory=SkillCapabilities)
    config: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
