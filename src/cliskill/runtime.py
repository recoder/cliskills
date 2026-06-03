"""Skill registration and execution runtime."""

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

import typer
from pydantic import BaseModel

from .manifest import create_manifest
from .models import OutputFormat, SkillCapabilities, SkillCommand, SkillManifest
from .renderers import render

P = ParamSpec("P")
R = TypeVar("R", bound=BaseModel)
CommandHandler = Callable[P, R]


class Skill:
    """Author-facing skill registration API."""

    def __init__(
        self,
        *,
        name: str,
        version: str,
        description: str,
        capabilities: SkillCapabilities | None = None,
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.capabilities = capabilities or SkillCapabilities()
        self._commands: dict[str, RegisteredCommand] = {}

    def command(
        self,
        *,
        name: str,
        description: str,
        input_model: type[BaseModel] | None = None,
        output_model: type[BaseModel] | None = None,
        formats: list[OutputFormat] | None = None,
        capabilities: SkillCapabilities | None = None,
    ) -> Callable[[CommandHandler[P, R]], CommandHandler[P, R]]:
        """Register a skill command function."""

        def decorator(function: CommandHandler[P, R]) -> CommandHandler[P, R]:
            if name in self._commands:
                raise ValueError(f"Command already registered: {name}")
            self._commands[name] = RegisteredCommand(
                function=cast(Callable[..., BaseModel], function),
                manifest=SkillCommand(
                    name=name,
                    description=description,
                    input_schema=_model_schema(input_model),
                    output_schema=_model_schema(output_model),
                    formats=formats or ["json", "markdown", "toon"],
                    capabilities=capabilities or SkillCapabilities(),
                ),
                input_model=input_model,
                output_model=output_model,
            )
            return function

        return decorator

    @property
    def commands(self) -> dict[str, SkillCommand]:
        """Return registered command metadata keyed by command name."""
        return {name: command.manifest for name, command in self._commands.items()}

    def manifest(self) -> SkillManifest:
        """Build the machine-readable manifest for this skill."""
        return create_manifest(
            name=self.name,
            version=self.version,
            description=self.description,
            commands=[command.manifest for command in self._commands.values()],
            capabilities=self.capabilities,
        )

    def typer_app(self) -> typer.Typer:
        """Create a Typer app exposing current meta-commands."""
        app = typer.Typer(
            add_completion=False,
            context_settings={"help_option_names": ["-h", "--help"]},
        )

        @app.callback()
        def cli() -> None:
            """Skill command group."""

        @app.command()
        def manifest(
            output_format: str = typer.Option("json", "--format", help="Output format."),
        ) -> None:
            """Emit the machine-readable skill manifest."""
            if output_format not in ("json", "markdown", "toon"):
                raise typer.BadParameter("Supported formats: json, markdown, toon.")
            typer.echo(render(self.manifest(), cast(OutputFormat, output_format)), nl=False)

        return app

    def main(self) -> None:
        """Run the skill CLI."""
        self.typer_app()()


class RegisteredCommand(BaseModel):
    """Internal command registration record."""

    function: Callable[..., BaseModel]
    manifest: SkillCommand
    input_model: type[BaseModel] | None
    output_model: type[BaseModel] | None

    model_config = {"arbitrary_types_allowed": True}


def _model_schema(model: type[BaseModel] | None) -> dict[str, Any] | None:
    if model is None:
        return None
    return model.model_json_schema()
