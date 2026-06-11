import json

from typer.testing import CliRunner

from examples.demo_skill.main import app


def test_demo_skill_commands_outputs_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["commands", "--format", "json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert len(output["commands"]) == 1
    assert output["commands"][0]["name"] == "echo"
    assert output["commands"][0]["description"] == "Echo text and report its length."
    assert output["commands"][0]["formats"] == ["json", "markdown", "toon"]


def test_demo_skill_commands_outputs_markdown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["commands", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("```json\n")
    assert '"name": "echo"' in result.stdout
    assert '"description": "Echo text and report its length."' in result.stdout


def test_demo_skill_commands_outputs_toon(runner: CliRunner) -> None:
    result = runner.invoke(app, ["commands", "--format", "toon"])

    assert result.exit_code == 0
    assert (
        "commands[1]{name,description,input_schema,output_schema,formats,capabilities}:"
        in result.stdout
    )
    assert "echo,Echo text and report its length." in result.stdout


def test_demo_skill_commands_rejects_unsupported_format(runner: CliRunner) -> None:
    result = runner.invoke(app, ["commands", "--format", "yaml"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "commands"
    assert output["errors"][0]["code"] == "UNSUPPORTED_FORMAT"
