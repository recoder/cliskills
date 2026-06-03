"""Demo skill entry point."""

from typing import Annotated, cast

import typer

from cliskill import SkillCommand, create_manifest
from cliskill.renderers import OutputFormat, render

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def cli() -> None:
    """Demo skill command group."""


@app.command()
def manifest(
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format."),
    ] = "json",
) -> None:
    """Emit the machine-readable demo skill manifest."""
    if output_format not in ("json", "markdown", "toon"):
        raise typer.BadParameter("Supported formats: json, markdown, toon.")
    supported_format = cast(OutputFormat, output_format)

    demo_manifest = create_manifest(
        name="demo-skill",
        version="0.1.0",
        description="Demo skill for cliskill smoke tests.",
        commands=[
            SkillCommand(
                name="manifest",
                description="Emit the machine-readable skill manifest.",
            )
        ],
    )
    typer.echo(render(demo_manifest, supported_format), nl=False)


def main() -> None:
    """Run the demo skill CLI."""
    app()
