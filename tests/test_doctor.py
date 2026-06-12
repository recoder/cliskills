import json

from typer.testing import CliRunner

from examples.demo_skill.main import app, skill


def test_demo_skill_doctor_result() -> None:
    result = skill.doctor()

    assert result.ok is True
    assert result.command == "doctor"
    assert result.data == {
        "checks": [
            {
                "name": "contract",
                "ok": True,
                "message": "Skill contract is available.",
            }
        ]
    }
    assert result.errors == []
    assert result.metadata["skill_name"] == "demo-skill"
    assert result.metadata["skill_version"] == "0.1.0"


def test_demo_skill_doctor_outputs_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["doctor", "--format", "json"])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "doctor"
    assert output["data"]["checks"][0]["name"] == "contract"
    assert output["data"]["checks"][0]["ok"] is True
    assert output["errors"] == []
    assert output["metadata"]["skill_name"] == "demo-skill"


def test_demo_skill_doctor_outputs_markdown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["doctor", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("```json\n")
    assert '"command": "doctor"' in result.stdout
    assert '"name": "contract"' in result.stdout


def test_demo_skill_doctor_outputs_toon(runner: CliRunner) -> None:
    result = runner.invoke(app, ["doctor", "--format", "toon"])

    assert result.exit_code == 0
    assert "ok: true\n" in result.stdout
    assert "command: doctor\n" in result.stdout
    assert "checks[1]{name,ok,message}:\n" in result.stdout
    assert "contract,true,Skill contract is available.\n" in result.stdout


def test_demo_skill_doctor_rejects_unsupported_format(runner: CliRunner) -> None:
    result = runner.invoke(app, ["doctor", "--format", "yaml"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "doctor"
    assert output["errors"][0]["code"] == "UNSUPPORTED_FORMAT"
