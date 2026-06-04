"""Skill registration and execution runtime."""

import json
import os
from collections.abc import Callable
from inspect import Parameter, signature
from typing import Any, ParamSpec, TypeVar, cast

import typer
from pydantic import BaseModel, ValidationError

from .context import SkillContext
from .manifest import create_manifest
from .models import OutputFormat, SkillCapabilities, SkillCommand, SkillManifest, SkillResult
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

    def run(self, command_name: str, json_input: str) -> SkillResult:
        """Run a registered command with JSON input."""
        registered_command = self._commands.get(command_name)
        if registered_command is None:
            raise ValueError(f"Command not found: {command_name}")

        try:
            input_data = json.loads(json_input)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON input: {error.msg}") from error

        if registered_command.input_model is not None:
            command_input = registered_command.input_model.model_validate(input_data)
        else:
            command_input = None

        ctx = SkillContext(environment=os.environ)
        result = _call_command(registered_command, command_input, ctx)

        if registered_command.output_model is not None:
            output = registered_command.output_model.model_validate(result)
            return _success_result(command_name, output)
        if isinstance(result, BaseModel):
            return _success_result(command_name, result)
        raise TypeError(f"Command returned unsupported result type: {type(result).__name__}")

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

        @app.command()
        def run(
            command_name: str = typer.Argument(..., help="Registered command name."),
            json_input: str = typer.Option(..., "--json", help="JSON command input."),
            output_format: str = typer.Option("json", "--format", help="Output format."),
        ) -> None:
            """Run a registered skill command."""
            if output_format not in ("json", "markdown", "toon"):
                raise typer.BadParameter("Supported formats: json, markdown, toon.")
            try:
                result = self.run(command_name, json_input)
            except (TypeError, ValueError, ValidationError) as error:
                raise typer.BadParameter(str(error)) from error
            typer.echo(render(result, cast(OutputFormat, output_format)), nl=False)

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


def _success_result(command_name: str, output: BaseModel) -> SkillResult:
    return SkillResult(
        ok=True,
        command=command_name,
        data=output.model_dump(mode="json"),
    )


def _call_command(
    registered_command: RegisteredCommand,
    command_input: BaseModel | None,
    ctx: SkillContext,
) -> BaseModel:
    parameters = signature(registered_command.function).parameters
    arguments: list[Any] = []

    for parameter in parameters.values():
        if parameter.kind not in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.KEYWORD_ONLY,
        ):
            continue
        if parameter.annotation is SkillContext:
            arguments.append(ctx)
        elif command_input is not None:
            arguments.append(command_input)
        elif parameter.default is Parameter.empty:
            raise TypeError(f"Cannot satisfy required parameter: {parameter.name}")

    return registered_command.function(*arguments)
