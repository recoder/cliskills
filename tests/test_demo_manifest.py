import json

import pytest
from pydantic import BaseModel
from typer.testing import CliRunner

from cliskill import Skill, SkillContext
from examples.demo_skill.main import app, skill


class SampleInput(BaseModel):
    value: str


class SampleOutput(BaseModel):
    value: str


def test_demo_skill_manifest_outputs_json() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["manifest", "--format", "json"])

    assert result.exit_code == 0
    manifest = json.loads(result.stdout)
    assert manifest["name"] == "demo-skill"
    assert manifest["version"] == "0.1.0"
    assert manifest["contract_version"] == "0.1"
    assert manifest["commands"][0]["name"] == "echo"
    assert manifest["commands"][0]["input_schema"]["properties"]["text"]["type"] == "string"
    assert manifest["commands"][0]["output_schema"]["properties"]["length"]["type"] == "integer"
    assert manifest["commands"][0]["formats"] == ["json", "markdown", "toon"]
    assert manifest["capabilities"]["network_access"] is False


def test_demo_skill_manifest_outputs_markdown() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["manifest", "--format", "markdown"])

    assert result.exit_code == 0
    assert result.stdout.startswith("# demo-skill\n")
    assert "| `echo` | Echo text and report its length. |" in result.stdout
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


def test_skill_command_decorator_registers_command_schema() -> None:
    registered_skill = Skill(
        name="test-skill",
        version="0.1.0",
        description="Test skill.",
    )

    @registered_skill.command(
        name="test",
        description="Test command.",
        input_model=SampleInput,
        output_model=SampleOutput,
    )
    def test_command(input_data: SampleInput, ctx: SkillContext) -> SampleOutput:
        return SampleOutput(value=input_data.value)

    manifest = registered_skill.manifest()

    assert list(registered_skill.commands) == ["test"]
    assert manifest.commands[0].name == "test"
    assert manifest.commands[0].input_schema is not None
    assert manifest.commands[0].input_schema["properties"]["value"]["type"] == "string"
    assert manifest.commands[0].output_schema is not None
    assert manifest.commands[0].output_schema["properties"]["value"]["type"] == "string"


def test_skill_rejects_duplicate_command_names() -> None:
    registered_skill = Skill(
        name="test-skill",
        version="0.1.0",
        description="Test skill.",
    )

    @registered_skill.command(name="test", description="Test command.")
    def first_command() -> SampleOutput:
        return SampleOutput(value="first")

    with pytest.raises(ValueError, match="Command already registered: test"):

        @registered_skill.command(name="test", description="Duplicate command.")
        def second_command() -> SampleOutput:
            return SampleOutput(value="second")


def test_demo_skill_exposes_registered_echo_command() -> None:
    assert list(skill.commands) == ["echo"]


def test_demo_skill_run_echo_outputs_json() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "echo", "--json", '{"text":"hello"}', "--format", "json"],
    )

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output == {
        "artifacts": [],
        "command": "echo",
        "data": {"length": 5, "text": "hello"},
        "errors": [],
        "metadata": {},
        "ok": True,
        "warnings": [],
    }


def test_demo_skill_run_echo_outputs_markdown() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "echo", "--json", '{"text":"hello"}', "--format", "markdown"],
    )

    assert result.exit_code == 0
    assert result.stdout.startswith("```json\n")
    assert '"command": "echo"' in result.stdout
    assert '"ok": true' in result.stdout
    assert '"length": 5' in result.stdout
    assert '"text": "hello"' in result.stdout


def test_demo_skill_run_echo_outputs_toon() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "echo", "--json", '{"text":"hello"}', "--format", "toon"],
    )

    assert result.exit_code == 0
    assert "ok: true\n" in result.stdout
    assert "command: echo\n" in result.stdout
    assert "data:\n  text: hello\n  length: 5\n" in result.stdout
    assert "errors: []\n" in result.stdout


def test_demo_skill_run_rejects_missing_command() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "missing", "--json", "{}", "--format", "json"],
    )

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "missing"
    assert output["data"] is None
    assert output["errors"][0]["code"] == "COMMAND_NOT_FOUND"
    assert output["errors"][0]["message"] == "Command not found: missing"


def test_demo_skill_run_rejects_invalid_input() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "echo", "--json", "{}", "--format", "json"],
    )

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "echo"
    assert output["data"] is None
    assert output["errors"][0]["code"] == "VALIDATION_ERROR"
    assert output["errors"][0]["field"] == "text"
    assert output["errors"][0]["message"] == "Field required"


def test_demo_skill_run_rejects_invalid_json() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "echo", "--json", "{", "--format", "json"],
    )

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "echo"
    assert output["errors"][0]["code"] == "VALIDATION_ERROR"
    assert (
        output["errors"][0]["message"]
        == "Invalid JSON input: Expecting property name enclosed in double quotes"
    )


def test_demo_skill_run_rejects_unsupported_format_with_json_envelope() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["run", "echo", "--json", '{"text":"hello"}', "--format", "yaml"],
    )

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "echo"
    assert output["errors"][0]["code"] == "UNSUPPORTED_FORMAT"
    assert output["errors"][0]["field"] == "format"
