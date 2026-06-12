"""Core contract models."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer

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


class SkillCommands(BaseModel):
    """Registered operational commands for a skill."""

    commands: list[SkillCommand] = Field(default_factory=list)


class SkillConfigRequirement(BaseModel):
    """Declared configuration requirement for a skill."""

    name: str
    description: str
    required: bool = False
    default: Any | None = None
    secret: bool = False
    source: str | None = None

    @field_serializer("default")
    def serialize_default(self, value: Any | None) -> Any | None:
        """Redact secret defaults from generated contract output."""
        if self.secret and value is not None:
            return "[REDACTED]"
        return value


class SkillConfigSchema(BaseModel):
    """Declared configuration schema for a skill."""

    config: list[SkillConfigRequirement] = Field(default_factory=list)


class SkillConfigExample(BaseModel):
    """Example configuration payloads for a skill."""

    env: dict[str, str] = Field(default_factory=dict)
    json_config: dict[str, Any] = Field(
        default_factory=dict,
        serialization_alias="json",
        validation_alias="json",
    )


class SkillSchema(BaseModel):
    """Input and output schemas for one skill command."""

    command: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class SkillVersion(BaseModel):
    """Framework and skill version information."""

    framework_name: str = "cliskill"
    framework_version: str
    skill_name: str
    skill_version: str
    contract_version: str = "0.1"


class SkillError(BaseModel):
    """Structured error returned by operational commands."""

    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class SkillArtifact(BaseModel):
    """Artifact produced by an operational command."""

    path: str
    description: str | None = None
    media_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillResult(BaseModel):
    """Standard result envelope for operational commands."""

    ok: bool
    command: str
    data: dict[str, Any] | list[Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[SkillError] = Field(default_factory=list)
    artifacts: list[SkillArtifact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
