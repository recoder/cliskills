"""Demo skill entry point."""

from pydantic import BaseModel

from cliskill import Skill, SkillContext

skill = Skill(
    name="demo-skill",
    version="0.1.0",
    description="Demo skill for cliskill smoke tests.",
)


class EchoInput(BaseModel):
    """Input for the demo echo command."""

    text: str


class EchoOutput(BaseModel):
    """Output for the demo echo command."""

    text: str
    length: int


@skill.command(
    name="echo",
    description="Echo text and report its length.",
    input_model=EchoInput,
    output_model=EchoOutput,
)
def echo(input_data: EchoInput, ctx: SkillContext) -> EchoOutput:
    """Echo text and report its length."""
    return EchoOutput(text=input_data.text, length=len(input_data.text))


app = skill.typer_app()


def main() -> None:
    """Run the demo skill CLI."""
    skill.main()
