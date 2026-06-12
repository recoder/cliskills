import json

from typer import Typer
from typer.testing import CliRunner

from cliskill import Skill, SkillConfigRequirement
from examples.demo_skill.main import app


def test_demo_skill_config_schema_outputs_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "schema", "--format", "json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output == {"config": []}


def test_demo_skill_config_schema_outputs_markdown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "schema", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("```json\n")
    assert '"config": []' in result.stdout


def test_demo_skill_config_schema_outputs_toon(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "schema", "--format", "toon"])

    assert result.exit_code == 0
    assert result.stdout == "config: []\n"


def test_demo_skill_config_schema_rejects_unsupported_format(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "schema", "--format", "yaml"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "config schema"
    assert output["errors"][0]["code"] == "UNSUPPORTED_FORMAT"


def test_config_schema_redacts_secret_defaults_in_json(runner: CliRunner) -> None:
    config_app = _configured_skill_app()

    result = runner.invoke(config_app, ["config", "schema", "--format", "json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output["config"][0]["default"] == "https://api.example.test"
    assert output["config"][1]["default"] == "[REDACTED]"
    assert "super-secret-token" not in result.stdout


def test_config_schema_redacts_secret_defaults_in_markdown(runner: CliRunner) -> None:
    config_app = _configured_skill_app()

    result = runner.invoke(config_app, ["config", "schema", "--format", "markdown"])

    assert result.exit_code == 0
    assert "[REDACTED]" in result.stdout
    assert "super-secret-token" not in result.stdout


def test_config_schema_redacts_secret_defaults_in_toon(runner: CliRunner) -> None:
    config_app = _configured_skill_app()

    result = runner.invoke(config_app, ["config", "schema", "--format", "toon"])

    assert result.exit_code == 0
    assert "[REDACTED]" in result.stdout
    assert "super-secret-token" not in result.stdout


def test_demo_skill_config_example_outputs_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "example", "--format", "json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output == {"env": {}, "json": {}}


def test_demo_skill_config_example_outputs_markdown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "example", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("```json\n")
    assert '"env": {}' in result.stdout
    assert '"json": {}' in result.stdout


def test_demo_skill_config_example_outputs_toon(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "example", "--format", "toon"])

    assert result.exit_code == 0
    assert "env:\n" in result.stdout
    assert "json:\n" in result.stdout


def test_demo_skill_config_example_rejects_unsupported_format(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "example", "--format", "yaml"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "config example"
    assert output["errors"][0]["code"] == "UNSUPPORTED_FORMAT"


def _configured_skill_app() -> Typer:
    skill = Skill(
        name="configured-skill",
        version="0.1.0",
        description="Configured skill.",
        config=[
            SkillConfigRequirement(
                name="API_URL",
                description="Base API URL.",
                default="https://api.example.test",
                source="env",
            ),
            SkillConfigRequirement(
                name="API_TOKEN",
                description="API token.",
                default="super-secret-token",
                secret=True,
                source="env",
            ),
        ],
    )
    return skill.typer_app()
