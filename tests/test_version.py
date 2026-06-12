import json

from typer.testing import CliRunner

from examples.demo_skill.main import app, skill


def test_demo_skill_version_info() -> None:
    version_info = skill.version_info()

    assert version_info.framework_name == "cliskill"
    assert version_info.framework_version != ""
    assert version_info.skill_name == "demo-skill"
    assert version_info.skill_version == "0.1.0"
    assert version_info.contract_version == "0.1"


def test_demo_skill_version_outputs_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version", "--format", "json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output["framework_name"] == "cliskill"
    assert output["framework_version"] != ""
    assert output["skill_name"] == "demo-skill"
    assert output["skill_version"] == "0.1.0"
    assert output["contract_version"] == "0.1"


def test_demo_skill_version_outputs_markdown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("```json\n")
    assert '"framework_name": "cliskill"' in result.stdout
    assert '"skill_name": "demo-skill"' in result.stdout


def test_demo_skill_version_outputs_toon(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version", "--format", "toon"])

    assert result.exit_code == 0
    assert "framework_name: cliskill\n" in result.stdout
    assert "skill_name: demo-skill\n" in result.stdout


def test_demo_skill_version_rejects_unsupported_format(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version", "--format", "yaml"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "version"
    assert output["errors"][0]["code"] == "UNSUPPORTED_FORMAT"
