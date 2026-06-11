import json

from typer.testing import CliRunner

from examples.demo_skill.main import app


def test_demo_skill_schema_outputs_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["schema", "echo", "--format", "json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output["command"] == "echo"
    assert output["input_schema"]["properties"]["text"]["type"] == "string"
    assert output["output_schema"]["properties"]["length"]["type"] == "integer"


def test_demo_skill_schema_outputs_markdown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["schema", "echo", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("```json\n")
    assert '"command": "echo"' in result.stdout
    assert '"input_schema"' in result.stdout
    assert '"output_schema"' in result.stdout


def test_demo_skill_schema_outputs_toon(runner: CliRunner) -> None:
    result = runner.invoke(app, ["schema", "echo", "--format", "toon"])

    assert result.exit_code == 0
    assert "command: echo\n" in result.stdout
    assert "input_schema:\n" in result.stdout
    assert "output_schema:\n" in result.stdout


def test_demo_skill_schema_rejects_missing_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["schema", "missing", "--format", "json"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "missing"
    assert output["errors"][0]["code"] == "COMMAND_NOT_FOUND"
