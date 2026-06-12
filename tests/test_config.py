import json

from typer.testing import CliRunner

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
