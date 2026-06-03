import json

from typer.testing import CliRunner

from examples.demo_skill.main import app


def test_demo_skill_manifest_outputs_json() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["manifest", "--format", "json"])

    assert result.exit_code == 0
    manifest = json.loads(result.stdout)
    assert manifest["name"] == "demo-skill"
    assert manifest["version"] == "0.1.0"
    assert manifest["contract_version"] == "0.1"
    assert manifest["commands"][0]["name"] == "manifest"
    assert manifest["commands"][0]["formats"] == ["json", "markdown", "toon"]
    assert manifest["capabilities"]["network_access"] is False


def test_demo_skill_manifest_outputs_markdown() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["manifest", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("# demo-skill\n")
    assert "| `manifest` | Emit the machine-readable skill manifest. |" in result.stdout
    assert "`network_access`: `false`" in result.stdout


def test_demo_skill_manifest_outputs_toon() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["manifest", "--format", "toon"])

    assert result.exit_code == 0
    assert "name: demo-skill\n" in result.stdout
    assert (
        "commands[1]{name,description,input_schema,output_schema,formats,capabilities}:"
        in result.stdout
    )
    assert "network_access: false\n" in result.stdout
