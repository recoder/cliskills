from pydantic import BaseModel
from typer import Typer
from typer.testing import CliRunner

from cliskill import Skill, SkillConfigRequirement, SkillContext
from examples.demo_skill.main import app


class SampleInput(BaseModel):
    value: str


class SampleOutput(BaseModel):
    value: str


def test_demo_skill_md_outputs_generated_markdown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["skill-md"])

    assert result.exit_code == 0
    assert result.stdout.startswith("# demo-skill\n")
    assert "Demo skill for cliskill smoke tests." in result.stdout
    assert "## Contract\n" in result.stdout
    assert "- Skill version: `0.1.0`" in result.stdout
    assert "- Contract version: `0.1`" in result.stdout
    assert "### `echo`\n" in result.stdout
    assert "Echo text and report its length." in result.stdout
    assert '"text"' in result.stdout
    assert '"length"' in result.stdout
    assert "## Configuration\n" in result.stdout
    assert "No configuration required." in result.stdout
    assert "## Capabilities\n" in result.stdout
    assert "`network_access`: `false`" in result.stdout


def test_skill_md_redacts_secret_config_defaults(runner: CliRunner) -> None:
    result = runner.invoke(_configured_skill_app(), ["skill-md"])

    assert result.exit_code == 0
    assert "| `API_TOKEN` | `true` | `true` | env | [REDACTED] | API token. |" in result.stdout
    assert "super-secret-token" not in result.stdout


def _configured_skill_app() -> Typer:
    skill = Skill(
        name="configured-skill",
        version="0.1.0",
        description="Configured skill.",
        config=[
            SkillConfigRequirement(
                name="API_TOKEN",
                description="API token.",
                required=True,
                default="super-secret-token",
                secret=True,
                source="env",
            ),
        ],
    )

    @skill.command(
        name="sample",
        description="Sample command.",
        input_model=SampleInput,
        output_model=SampleOutput,
    )
    def sample(input_data: SampleInput, ctx: SkillContext) -> SampleOutput:
        return SampleOutput(value=input_data.value)

    return skill.typer_app()
