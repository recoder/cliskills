"""Skill registration and execution runtime."""

import json
import os
import sys
from collections.abc import Callable
from inspect import Parameter, signature
from typing import Any, ParamSpec, TypeVar, cast

import typer
from pydantic import BaseModel, ValidationError

from .context import SkillContext
from .manifest import create_manifest
from .models import (
    OutputFormat,
    SkillCapabilities,
    SkillCommand,
    SkillCommands,
    SkillConfigExample,
    SkillConfigSchema,
    SkillError,
    SkillManifest,
    SkillResult,
    SkillSchema,
)
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

    def command_list(self) -> SkillCommands:
        """Return registered operational command metadata."""
        return SkillCommands(commands=[command.manifest for command in self._commands.values()])

    def config_schema(self) -> SkillConfigSchema:
        """Return declared skill configuration requirements."""
        return SkillConfigSchema()

    def config_example(self) -> SkillConfigExample:
        """Return example skill configuration payloads."""
        return SkillConfigExample()

    def manifest(self) -> SkillManifest:
        """Build the machine-readable manifest for this skill."""
        return create_manifest(
            name=self.name,
            version=self.version,
            description=self.description,
            commands=[command.manifest for command in self._commands.values()],
            capabilities=self.capabilities,
        )

    def schema(self, command_name: str) -> SkillSchema:
        """Return input and output schemas for a registered command."""
        registered_command = self._commands.get(command_name)
        if registered_command is None:
            raise SkillRunError(_command_not_found_result(command_name))
        return SkillSchema(
            command=command_name,
            input_schema=registered_command.manifest.input_schema,
            output_schema=registered_command.manifest.output_schema,
        )

    def run(self, command_name: str, json_input: str) -> SkillResult:
        """Run a registered command with JSON input."""
        registered_command = self._commands.get(command_name)
        if registered_command is None:
            raise SkillRunError(_command_not_found_result(command_name))

        try:
            input_data = json.loads(json_input)
        except json.JSONDecodeError as error:
            raise SkillRunError(
                _failure_result(
                    command_name,
                    SkillError(
                        code="VALIDATION_ERROR",
                        message=f"Invalid JSON input: {error.msg}",
                        details={"position": error.pos},
                    ),
                )
            ) from error

        try:
            if registered_command.input_model is not None:
                command_input = registered_command.input_model.model_validate(input_data)
            else:
                command_input = None
        except ValidationError as error:
            raise SkillRunError(_validation_failure_result(command_name, error)) from error

        ctx = SkillContext(environment=os.environ)
        try:
            result = _call_command(registered_command, command_input, ctx)

            if registered_command.output_model is not None:
                output = registered_command.output_model.model_validate(result)
                return _success_result(command_name, output)
            if isinstance(result, BaseModel):
                return _success_result(command_name, result)
            raise TypeError(f"Command returned unsupported result type: {type(result).__name__}")
        except ValidationError as error:
            raise SkillRunError(_validation_failure_result(command_name, error)) from error
        except Exception as error:
            raise SkillRunError(
                _failure_result(
                    command_name,
                    SkillError(code="INTERNAL_ERROR", message=str(error)),
                )
            ) from error

    def typer_app(self) -> typer.Typer:
        """Create a Typer app exposing current meta-commands."""
        app = typer.Typer(
            add_completion=False,
            context_settings={"help_option_names": ["-h", "--help"]},
        )
        config_app = typer.Typer(
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
        def commands(
            output_format: str = typer.Option("json", "--format", help="Output format."),
        ) -> None:
            """List registered operational commands."""
            if output_format not in ("json", "markdown", "toon"):
                result = _unsupported_format_result("commands")
                typer.echo(render(result, "json"), nl=False)
                raise typer.Exit(1)
            typer.echo(render(self.command_list(), cast(OutputFormat, output_format)), nl=False)

        @config_app.command("schema")
        def config_schema(
            output_format: str = typer.Option("json", "--format", help="Output format."),
        ) -> None:
            """Emit declared configuration requirements."""
            if output_format not in ("json", "markdown", "toon"):
                result = _unsupported_format_result("config schema")
                typer.echo(render(result, "json"), nl=False)
                raise typer.Exit(1)
            typer.echo(render(self.config_schema(), cast(OutputFormat, output_format)), nl=False)

        @config_app.command("example")
        def config_example(
            output_format: str = typer.Option("json", "--format", help="Output format."),
        ) -> None:
            """Emit example configuration payloads."""
            if output_format not in ("json", "markdown", "toon"):
                result = _unsupported_format_result("config example")
                typer.echo(render(result, "json"), nl=False)
                raise typer.Exit(1)
            typer.echo(render(self.config_example(), cast(OutputFormat, output_format)), nl=False)

        @app.command()
        def schema(
            command_name: str = typer.Argument(..., help="Registered command name."),
            output_format: str = typer.Option("json", "--format", help="Output format."),
        ) -> None:
            """Emit input and output schemas for a registered command."""
            if output_format not in ("json", "markdown", "toon"):
                result = _unsupported_format_result(command_name)
                typer.echo(render(result, "json"), nl=False)
                raise typer.Exit(1)
            try:
                schema_result = self.schema(command_name)
            except SkillRunError as error:
                typer.echo(render(error.result, cast(OutputFormat, output_format)), nl=False)
                raise typer.Exit(1) from error
            typer.echo(render(schema_result, cast(OutputFormat, output_format)), nl=False)

        @app.command()
        def run(
            command_name: str = typer.Argument(..., help="Registered command name."),
            json_input: str | None = typer.Option(None, "--json", help="JSON command input."),
            use_stdin: bool = typer.Option(False, "--stdin", help="Read JSON input from stdin."),
            output_format: str = typer.Option("json", "--format", help="Output format."),
        ) -> None:
            """Run a registered skill command."""
            if output_format not in ("json", "markdown", "toon"):
                result = _unsupported_format_result(command_name)
                typer.echo(render(result, "json"), nl=False)
                raise typer.Exit(1)
            input_source_result = _resolve_run_input(command_name, json_input, use_stdin)
            if isinstance(input_source_result, SkillResult):
                typer.echo(render(input_source_result, cast(OutputFormat, output_format)), nl=False)
                raise typer.Exit(1)
            try:
                result = self.run(command_name, input_source_result)
            except SkillRunError as error:
                typer.echo(render(error.result, cast(OutputFormat, output_format)), nl=False)
                raise typer.Exit(1) from error
            typer.echo(render(result, cast(OutputFormat, output_format)), nl=False)

        app.add_typer(config_app, name="config")
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


class SkillRunError(Exception):
    """Internal exception carrying a structured run failure."""

    def __init__(self, result: SkillResult) -> None:
        super().__init__(result.errors[0].message if result.errors else "Skill run failed.")
        self.result = result


def _model_schema(model: type[BaseModel] | None) -> dict[str, Any] | None:
    if model is None:
        return None
    return model.model_json_schema()


def _success_result(command_name: str, output: BaseModel) -> SkillResult:
    return SkillResult(
        ok=True,
        command=command_name,
        data=output.model_dump(mode="json", by_alias=True),
    )


def _failure_result(command_name: str, error: SkillError) -> SkillResult:
    return SkillResult(
        ok=False,
        command=command_name,
        data=None,
        errors=[error],
    )


def _command_not_found_result(command_name: str) -> SkillResult:
    return _failure_result(
        command_name,
        SkillError(
            code="COMMAND_NOT_FOUND",
            message=f"Command not found: {command_name}",
        ),
    )


def _unsupported_format_result(command_name: str) -> SkillResult:
    return _failure_result(
        command_name,
        SkillError(
            code="UNSUPPORTED_FORMAT",
            message="Supported formats: json, markdown, toon.",
            field="format",
        ),
    )


def _input_source_failure_result(command_name: str, message: str) -> SkillResult:
    return _failure_result(
        command_name,
        SkillError(
            code="VALIDATION_ERROR",
            message=message,
            field="input",
        ),
    )


def _resolve_run_input(
    command_name: str,
    json_input: str | None,
    use_stdin: bool,
) -> str | SkillResult:
    if json_input is not None and use_stdin:
        return _input_source_failure_result(
            command_name,
            "Use exactly one input source: --json or --stdin.",
        )
    if json_input is None and not use_stdin:
        return _input_source_failure_result(
            command_name,
            "Missing input source. Provide --json or --stdin.",
        )
    if use_stdin:
        return sys.stdin.read()
    if json_input is None:
        return _input_source_failure_result(
            command_name,
            "Missing input source. Provide --json or --stdin.",
        )
    return json_input


def _validation_failure_result(command_name: str, error: ValidationError) -> SkillResult:
    first_error = error.errors()[0]
    location = ".".join(str(part) for part in first_error.get("loc", ()))
    return _failure_result(
        command_name,
        SkillError(
            code="VALIDATION_ERROR",
            message=str(first_error.get("msg", "Input is invalid.")),
            field=location or None,
            details={"errors": error.errors()},
        ),
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
