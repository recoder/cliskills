# AGENTS.md

# Agent Instructions for CLI Skills

This repository contains a Python framework for creating contract-first command-line tools intended to be used as LLM skills.

The project is tentatively named `cliskill`.

The main idea is simple: a skill is a normal CLI program, but it must expose machine-readable metadata, schemas, configuration requirements, safety/capability declarations, examples, tests, and generated documentation.

Agents working in this repository should optimize for correctness, boring reliability, and clean contracts over clever abstractions.

---

## Project Goals

Build a Python framework that helps developers create CLI tools that are:

- Discoverable by agents.
- Self-documenting.
- Schema-driven.
- Non-interactive by default.
- Easy to test.
- Safe to inspect before execution.
- Installable as normal Python packages.
- Usable from shell scripts, OpenClaw, and eventually MCP-style tool systems.

The framework should make this kind of interaction reliable:

```bash
demo-skill manifest --format json
```

```bash
demo-skill schema echo --format json
```

```bash
demo-skill run echo --json '{"text":"hello"}' --format json
```

```bash
demo-skill skill-md > SKILL.md
```

---

## Non-Goals for Early Versions

Do not turn this into a universal CLI framework.

Avoid these until the core contract is stable:

- Complex plugin dependency resolution.
- Remote skill execution.
- Full sandboxing.
- Skill marketplaces.
- Automatic code generation by agents.
- Rich terminal UI.
- Interactive prompts.
- Too many output formats.
- Custom DSLs.

Prefer a small, boring core that works.

---

## Expected Repository Layout

Use this layout unless the repository already has a different established structure:

```text
.
├── AGENTS.md
├── ROADMAP.md
├── README.md
├── pyproject.toml
├── src/
│   └── cliskill/
│       ├── __init__.py
│       ├── app.py
│       ├── context.py
│       ├── errors.py
│       ├── manifest.py
│       ├── models.py
│       ├── renderers.py
│       ├── runtime.py
│       └── testing.py
├── examples/
│   └── demo_skill/
├── tests/
└── docs/
```

If you change the layout, update this file and `README.md`.

---

## Design Principles

### Contract First

The manifest and schemas are the source of truth.

Human-readable documentation should be generated from structured metadata whenever possible.

Do not make agents parse prose when structured data can be emitted instead.

### JSON First

JSON-compatible data is the canonical interface.

Markdown, YAML, CSV, TOON, or plain text may be useful later, but they are derived formats.

Every command intended for agent use should support JSON output.

### Non-Interactive by Default

Commands must not block waiting for user input unless explicitly designed for human use.

Agent-facing commands should accept arguments, JSON payloads, stdin, config, or files — not prompts.

### Stable Result Envelope

Operational commands should return a standard result envelope:

```json
{
  "ok": true,
  "command": "example",
  "data": {},
  "warnings": [],
  "errors": [],
  "artifacts": [],
  "metadata": {}
}
```

Failed commands should return structured errors:

```json
{
  "ok": false,
  "command": "example",
  "data": null,
  "warnings": [],
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Input is invalid.",
      "field": "name",
      "details": {}
    }
  ],
  "artifacts": [],
  "metadata": {}
}
```

### Explicit Capabilities

Skills should declare their behavior before execution.

Important capability dimensions:

- filesystem read
- filesystem write
- file deletion
- network access
- secret access
- subprocess execution
- destructive operations
- generated artifacts

Do not hide side effects.

### Generated Documentation

`SKILL.md` should be generated from the skill contract.

Do not manually duplicate command schemas in documentation unless unavoidable.

---

## Coding Style

Use modern, idiomatic Python.

Preferred baseline:

- Python 3.11+.
- `pydantic` for data models and schema generation.
- `typer` or `click` for CLI wiring.
- `pytest` for tests.
- `ruff` for linting and formatting.
- Type annotations everywhere practical.

Keep modules small and focused.

Prefer explicit names over clever names.

Prefer simple data models over inheritance-heavy designs.

Avoid hidden global state.

Avoid magic behavior that makes skill execution hard to reason about.

---

## Public API Style

The desired authoring style should be close to this:

```python
from pydantic import BaseModel
from cliskill import Skill, SkillContext

skill = Skill(
    name="demo",
    version="0.1.0",
    description="Demo skill."
)

class EchoInput(BaseModel):
    text: str

class EchoOutput(BaseModel):
    text: str
    length: int

@skill.command(
    name="echo",
    description="Echo text and report its length.",
    input_model=EchoInput,
    output_model=EchoOutput,
)
def echo(input: EchoInput, ctx: SkillContext) -> EchoOutput:
    return EchoOutput(text=input.text, length=len(input.text))

if __name__ == "__main__":
    skill.main()
```

Do not over-engineer this API before the basic flow works.

---

## Standard Commands

Every skill should eventually expose these standard commands:

```text
manifest
commands
schema
config schema
config example
doctor
examples
run-example
skill-md
test
version
run
```

The most important early commands are:

```text
manifest
schema
run
skill-md
doctor
```

Start there.

---

## Testing Expectations

Every meaningful change should include tests.

Prioritize tests for:

- manifest generation
- JSON Schema generation
- command registration
- command execution
- result envelope formatting
- exception normalization
- config schema generation
- `doctor` behavior
- `skill-md` generation

Use golden files when testing generated Markdown or JSON contracts.

Prefer deterministic tests.

Do not require network access in tests unless explicitly marked and skipped by default.

---

## Error Handling

Errors should be useful to both humans and agents.

Prefer structured error codes such as:

```text
VALIDATION_ERROR
COMMAND_NOT_FOUND
CONFIG_MISSING
DEPENDENCY_MISSING
INPUT_FILE_NOT_FOUND
OUTPUT_WRITE_FAILED
UNSUPPORTED_FORMAT
INTERNAL_ERROR
```

Do not print Python tracebacks to stdout in normal agent-facing output.

Tracebacks may be available in debug mode, but structured errors should remain the default.

---

## Output Rules

For command output:

- stdout is for machine-readable result data.
- stderr is for logs, diagnostics, progress, and debug information.
- JSON output should be valid JSON and nothing else.
- Failed commands should use non-zero exit codes.
- Do not mix logs with JSON stdout.

---

## Configuration Rules

Skills should declare configuration requirements explicitly.

Configuration metadata should include:

- name
- description
- required/optional
- default value, if any
- whether the value is secret
- source, such as environment variable or config file

Secrets must be redacted from generated output.

Never print raw secret values in test output, doctor output, errors, or generated docs.

---

## Documentation Rules

Keep documentation practical.

Generated docs should include:

- skill purpose
- commands
- input schemas
- output schemas
- config variables
- capabilities/safety notes
- examples
- artifact behavior

When writing Markdown in this repository, keep examples copy-pasteable.

---

## Dependency Policy

Be conservative with dependencies.

A dependency is acceptable if it clearly simplifies core functionality.

Avoid dependencies for tiny helpers.

Do not add heavyweight frameworks without a strong reason.

---

## Agent Workflow

When making changes:

1. Inspect existing files first.
2. Keep changes focused.
3. Update tests with behavior changes.
4. Update docs when public behavior changes.
5. Run relevant tests if possible.
6. Report what changed and what was not verified.

Do not claim tests passed unless they were actually run.

If the repository is not initialized yet, create the minimal useful skeleton rather than a large speculative structure.

---

## Quality Bar

A feature is not done until:

- It has a clear public behavior.
- It has tests or a good reason tests are deferred.
- It works without interactive input.
- It produces structured output where appropriate.
- It does not break existing generated docs or schemas.
- It avoids unnecessary dependencies and abstractions.

---

## First Implementation Target

The first milestone should make this possible:

```bash
demo-skill manifest --format json
```

The second milestone should make this possible:

```bash
demo-skill run echo --json '{"text":"hello"}' --format json
```

The third milestone should make this possible:

```bash
demo-skill skill-md > SKILL.md
```

Everything else can wait.
