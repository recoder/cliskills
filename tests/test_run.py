import json

from typer.testing import CliRunner

from examples.demo_skill.main import app


def test_demo_skill_run_echo_outputs_json(runner: CliRunner) -> None:
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


def test_demo_skill_run_echo_accepts_stdin(runner: CliRunner) -> None:
    result = runner.invoke(
        app,
        ["run", "echo", "--stdin", "--format", "json"],
        input='{"text":"hello"}',
    )

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "echo"
    assert output["data"] == {"length": 5, "text": "hello"}


def test_demo_skill_run_echo_outputs_markdown(runner: CliRunner) -> None:
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


def test_demo_skill_run_echo_outputs_toon(runner: CliRunner) -> None:
    result = runner.invoke(
        app,
        ["run", "echo", "--json", '{"text":"hello"}', "--format", "toon"],
    )

    assert result.exit_code == 0
    assert "ok: true\n" in result.stdout
    assert "command: echo\n" in result.stdout
    assert "data:\n  text: hello\n  length: 5\n" in result.stdout
    assert "errors: []\n" in result.stdout


def test_demo_skill_run_rejects_missing_command(runner: CliRunner) -> None:
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


def test_demo_skill_run_rejects_invalid_input(runner: CliRunner) -> None:
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


def test_demo_skill_run_rejects_invalid_json(runner: CliRunner) -> None:
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


def test_demo_skill_run_rejects_missing_input_source(runner: CliRunner) -> None:
    result = runner.invoke(app, ["run", "echo", "--format", "json"])

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "echo"
    assert output["errors"][0]["code"] == "VALIDATION_ERROR"
    assert output["errors"][0]["field"] == "input"
    assert output["errors"][0]["message"] == "Missing input source. Provide --json or --stdin."


def test_demo_skill_run_rejects_multiple_input_sources(runner: CliRunner) -> None:
    result = runner.invoke(
        app,
        ["run", "echo", "--json", '{"text":"hello"}', "--stdin", "--format", "json"],
        input='{"text":"stdin"}',
    )

    assert result.exit_code == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "echo"
    assert output["errors"][0]["code"] == "VALIDATION_ERROR"
    assert output["errors"][0]["field"] == "input"
    assert output["errors"][0]["message"] == "Use exactly one input source: --json or --stdin."


def test_demo_skill_run_rejects_unsupported_format_with_json_envelope(
    runner: CliRunner,
) -> None:
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
