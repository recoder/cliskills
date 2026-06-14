import json
from typing import Any, cast

from typer import Typer
from typer.testing import CliRunner

from cliskill import Skill, SkillConfigRequirement, SkillResult
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


def test_doctor_fails_when_required_env_config_is_missing() -> None:
    configured_skill = _configured_skill()

    result = configured_skill.doctor(environment={})

    assert result.ok is False
    assert result.command == "doctor"
    assert result.errors[0].code == "CONFIG_MISSING"
    assert result.errors[0].field == "API_TOKEN"
    assert result.errors[0].details == {"source": "env"}
    checks = _doctor_checks(result)
    assert checks[1] == {
        "name": "config:API_TOKEN",
        "ok": False,
        "message": "Required environment variable is missing.",
        "field": "API_TOKEN",
        "required": True,
        "secret": True,
        "source": "env",
    }


def test_doctor_passes_when_required_env_config_is_present() -> None:
    configured_skill = _configured_skill()

    result = configured_skill.doctor(environment={"API_TOKEN": "super-secret-token"})

    assert result.ok is True
    assert result.errors == []
    checks = _doctor_checks(result)
    assert checks[1]["ok"] is True
    assert checks[1]["message"] == "Environment variable is set."


def test_doctor_does_not_emit_secret_values(runner: CliRunner) -> None:
    result = runner.invoke(
        _configured_skill_app(),
        ["doctor", "--format", "json"],
        env={"API_TOKEN": "super-secret-token"},
    )

    assert result.exit_code == 0
    assert "super-secret-token" not in result.stdout
    output = json.loads(result.stdout)
    assert output["data"]["checks"][1]["secret"] is True


def test_doctor_allows_optional_missing_env_config() -> None:
    configured_skill = Skill(
        name="configured-skill",
        version="0.1.0",
        description="Configured skill.",
        config=[
            SkillConfigRequirement(
                name="OPTIONAL_TOKEN",
                description="Optional token.",
                source="env",
            ),
        ],
    )

    result = configured_skill.doctor(environment={})

    assert result.ok is True
    assert result.errors == []
    assert _doctor_checks(result)[1]["message"] == "Optional environment variable is not set."


def test_doctor_allows_missing_env_config_with_default() -> None:
    configured_skill = Skill(
        name="configured-skill",
        version="0.1.0",
        description="Configured skill.",
        config=[
            SkillConfigRequirement(
                name="API_URL",
                description="Base API URL.",
                required=True,
                default="https://api.example.test",
                source="env",
            ),
        ],
    )

    result = configured_skill.doctor(environment={})

    assert result.ok is True
    assert result.errors == []
    assert _doctor_checks(result)[1]["message"] == "Default value is available."


def test_doctor_cli_exits_nonzero_when_required_env_config_is_missing(runner: CliRunner) -> None:
    result = runner.invoke(_configured_skill_app(), ["doctor", "--format", "json"], env={})

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["errors"][0]["code"] == "CONFIG_MISSING"


def _configured_skill() -> Skill:
    return Skill(
        name="configured-skill",
        version="0.1.0",
        description="Configured skill.",
        config=[
            SkillConfigRequirement(
                name="API_TOKEN",
                description="API token.",
                required=True,
                secret=True,
                source="env",
            ),
        ],
    )


def _configured_skill_app() -> Typer:
    return _configured_skill().typer_app()


def _doctor_checks(result: SkillResult) -> list[dict[str, Any]]:
    data = cast(dict[str, Any], result.data)
    return cast(list[dict[str, Any]], data["checks"])
