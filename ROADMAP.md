# ROADMAP.md

# CLI Skills Roadmap

CLI Skills is a Python framework for building contract-first command-line tools intended to be used by LLM agents and automation systems.

The project goal is not to create another generic CLI framework. The goal is to make local tools discoverable, inspectable, testable, installable, and safe enough for assistants such as OpenClaw to use without guessing.

## Guiding Principles

- **Contract first**: every skill exposes a machine-readable manifest, command schemas, configuration requirements, capabilities, and result schemas.
- **Boring execution model**: commands should be deterministic, non-interactive, and easy to run from scripts or agents.
- **JSON as the canonical interface**: other formats may exist, but structured JSON-compatible data is the source of truth.
- **Generated documentation**: `SKILL.md`, help text, examples, and schema docs should be generated from the same contract.
- **Agent safety**: skills declare filesystem, network, secret, subprocess, and destructive-operation behavior.
- **Testability by default**: a skill should be able to validate itself with `doctor`, examples, and test fixtures.
- **Small core, useful extensions**: keep the framework focused and avoid becoming a universal plugin platform too early.

---

## Phase 0: Project Skeleton

Goal: establish a clean Python project that can be installed, tested, and extended.

### Features

- Create initial Python package, tentatively named `cliskill`.
- Use `pyproject.toml` with modern Python packaging.
- Choose baseline dependencies:
  - `pydantic` for schemas and validation.
  - `typer` or `click` for CLI wiring.
  - `pytest` for tests.
  - `ruff` for linting and formatting.
  - `mypy` or `pyright` for type checking.
- Define repository layout:
  - `src/cliskill/`
  - `tests/`
  - `examples/`
  - `docs/`
- Add basic CI-friendly commands:
  - install dev dependencies
  - run tests
  - run lint
  - run type checks
- Add a minimal demo skill for smoke testing.

### Deliverables

- Installable package.
- Basic test suite.
- Example skill that can print a manifest.
- Initial README with project purpose and quick start.

---

## Phase 1: Core Contract Model

Goal: define the internal model that all skills use.

### Features

- Define `SkillManifest` model.
- Define `SkillCommand` model.
- Define `SkillConfig` / config schema model.
- Define `SkillCapabilities` model.
- Define `SkillArtifact` model.
- Define standard result envelope:
  - `ok`
  - `command`
  - `data`
  - `warnings`
  - `errors`
  - `artifacts`
  - `metadata`
- Define standard error object:
  - `code`
  - `message`
  - `field`
  - `details`
- Generate JSON Schema from input and output models.
- Add version fields for both framework and skill contracts.

### Deliverables

- Stable Python data models.
- JSON Schema generation tests.
- Golden manifest fixture.
- Golden result-envelope fixture.

---

## Phase 2: Skill Runtime API

Goal: make it pleasant to write a skill in Python.

### Features

- Create a `Skill` class.
- Support command registration through decorators.
- Support typed input and output models.
- Support a `SkillContext` object with:
  - working directory
  - environment/config access
  - output/artifact helpers
  - logging/warning helpers
- Support command metadata:
  - name
  - description
  - input model
  - output model
  - examples
  - supported output formats
  - capability overrides
- Normalize command results into the standard result envelope.
- Normalize exceptions into structured errors.
- Make commands non-interactive by default.

### Example Target API

```python
from pathlib import Path
from pydantic import BaseModel
from cliskill import Skill, SkillContext

skill = Skill(
    name="demo",
    version="0.1.0",
    description="Demo CLI skill."
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

### Deliverables

- Decorator-based skill authoring API.
- Runtime execution tests.
- Error normalization tests.
- Demo skill using the public API.

---

## Phase 3: Standard Meta-Commands

Goal: every skill should expose the same introspection and maintenance commands automatically.

### Features

Add standard commands:

- `manifest`
  - Emit the full machine-readable skill manifest.
- `commands`
  - List available operational commands.
- `schema`
  - Emit input/output schemas for a skill or command.
- `config schema`
  - Emit required and optional configuration schema.
- `config example`
  - Emit example `.env`, JSON, or YAML config.
- `doctor`
  - Validate environment, dependencies, config, paths, and optional external binaries.
- `examples`
  - List runnable examples.
- `run-example`
  - Execute a named example.
- `skill-md`
  - Generate `SKILL.md` from the contract.
- `test`
  - Run skill-local tests or smoke tests.
- `version`
  - Print framework and skill versions.

### Deliverables

- Working meta-command layer.
- JSON output for every meta-command.
- Markdown output for documentation commands.
- Tests proving every skill receives the standard commands.

---

## Phase 4: Agent-Friendly Execution Interface

Goal: make skills easy and reliable for LLM agents to call.

### Features

- Add universal `run` command:

```bash
skill-name run command-name --json '{"field":"value"}'
```

- Support reading JSON input from stdin:

```bash
echo '{"field":"value"}' | skill-name run command-name --stdin
```

- Support writing structured output to stdout.
- Send logs and diagnostics to stderr.
- Ensure non-zero exit codes for failed commands.
- Support `--format json`, `--format markdown`, and later `--format yaml` / `--format csv`.
- Support `--output path` when a command produces a file artifact.
- Support dry-run metadata where possible.
- Support machine-readable command discovery without parsing human help text.

### Deliverables

- Stable agent execution protocol.
- Shell-based integration tests.
- Examples showing agent-safe command invocation.

---

## Phase 5: Configuration, Secrets, and Dependency Checks

Goal: make runtime requirements explicit and verifiable.

### Features

- Define config declaration API.
- Support environment variable declarations:
  - required
  - optional
  - secret
  - default
  - description
- Support filesystem path declarations.
- Support external binary declarations.
- Support network/API dependency declarations.
- Implement `doctor` checks.
- Redact secret values from output.
- Support `.env` loading as an optional convenience.
- Allow skills to define custom doctor checks.

### Deliverables

- Config schema support.
- Redaction tests.
- Doctor command tests.
- Example skill requiring an environment variable and external binary.

---

## Phase 6: Generated Documentation

Goal: generate useful documentation from the contract without duplicating content.

### Features

- Generate `SKILL.md`.
- Generate command reference docs.
- Generate config reference docs.
- Generate examples section.
- Generate safety/capabilities section.
- Generate supported output formats section.
- Generate artifact behavior docs.
- Support custom long-form notes while keeping schemas authoritative.

### Deliverables

- `skill-md` command.
- Markdown generator tests with golden files.
- Generated docs for demo skills.

---

## Phase 7: Example Skills

Goal: prove the framework against real-world tasks, not toy demos.

### Candidate Skills

- `markdown-skill`
  - validate Markdown structure
  - extract front matter
  - build article metadata
  - produce cleaned Markdown
- `asset-pack-skill`
  - validate album/track asset folders
  - inspect expected image dimensions
  - generate asset manifest
  - report missing thumbnails or banners
- `suno-prompt-skill`
  - validate prompt length and structure
  - normalize lyrics sections
  - produce style prompt variants
  - detect overly generic descriptors
- `file-inspector-skill`
  - inspect files
  - emit MIME type, size, hash, basic metadata
  - produce JSON/Markdown reports

### Deliverables

- At least one real useful skill maintained inside `examples/` or a sibling repository.
- End-to-end tests proving OpenClaw-style discovery and execution.
- Real generated `SKILL.md` output.

---

## Phase 8: OpenClaw Integration

Goal: let OpenClaw discover, install, inspect, and run CLI skills.

### Features

- Define skill discovery protocol:

```bash
some-skill manifest --format json
```

- Support local executable discovery.
- Support Python package entry point discovery.
- Support repository-based installation later.
- Add OpenClaw commands:
  - `openclaw skills discover`
  - `openclaw skills describe`
  - `openclaw skills doctor`
  - `openclaw skills test`
  - `openclaw skills run`
- Cache manifests with version checks.
- Validate skill capabilities before execution.
- Optionally deny destructive/network/subprocess skills unless allowed.

### Deliverables

- OpenClaw proof of concept.
- Skill discovery examples.
- Capability validation tests.

---

## Phase 9: Packaging and Skill Registry

Goal: make skills easy to distribute and install.

### Features

- Define package metadata convention:

```toml
[tool.cliskill]
name = "example-skill"
manifest = "example_skill:skill"
```

- Support Python entry points.
- Support local path installs.
- Support Git repository installs.
- Support version constraints.
- Support lockfile or manifest cache.
- Support skill templates:
  - minimal skill
  - file-processing skill
  - API-backed skill
  - report-generating skill

### Deliverables

- Skill package template.
- Cookiecutter/copier-style project generator, or a simple `cliskill new` command.
- Install/discover documentation.

---

## Phase 10: Sandboxing and Policy

Goal: make skill execution safer in agentic environments.

### Features

- Capability declaration enforcement.
- Optional allow/deny policy file.
- Read-only mode.
- Dry-run mode support where possible.
- Working-directory restrictions.
- Artifact output directory restrictions.
- Network-disabled policy mode.
- Secret access policy mode.
- Subprocess policy mode.

### Deliverables

- Policy schema.
- Runtime policy checks.
- Tests for denied filesystem/network/destructive behavior.

---

## Phase 11: MCP and Other Tooling Bridges

Goal: make CLI skills usable beyond a single assistant/runtime.

### Features

- Generate MCP tool definitions from skill manifests.
- Optional `mcp-server` wrapper for a skill.
- Generate OpenAPI-like descriptions where useful.
- Export tool metadata for other agent frameworks.
- Provide adapter examples.

### Deliverables

- Experimental MCP bridge.
- Example CLI skill exposed through MCP.
- Documentation for adapter authors.

---

## Phase 12: Advanced Output Formats and Token Efficiency

Goal: support compact and specialized formats only after the core contract is stable.

### Features

- Add YAML output.
- Add CSV output for tabular data.
- Add Markdown table rendering.
- Evaluate TOON or other token-efficient structured formats.
- Add output-format capability metadata per command.
- Allow commands to declare whether a format is lossless or lossy.

### Deliverables

- Format renderer abstraction.
- Format-specific tests.
- Clear documentation on canonical vs derived formats.

---

## Phase 13: Long-Term Ideas

These are intentionally not part of the MVP.

### Ideas

- Skill dependency graph.
- Skill composition/pipelines.
- Remote skill execution.
- Signed skill packages.
- Reproducible execution environments.
- Containerized skill runtime.
- Web UI for browsing installed skills.
- Built-in benchmark suite for agent usability.
- Automatic example generation.
- Automatic `SKILL.md` quality checks.
- Agent-authored skill patch workflow with required tests.

---

## Suggested MVP Definition

The first usable version should include only:

- Python package skeleton.
- Contract models.
- Decorator-based command registration.
- Standard result envelope.
- `manifest` command.
- `schema` command.
- `run` command with JSON input.
- `skill-md` generation.
- `doctor` stub.
- One real example skill.
- Tests for the above.

A good first milestone is this command working reliably:

```bash
demo-skill manifest --format json
```

A good second milestone is this command working reliably:

```bash
demo-skill run echo --json '{"text":"hello"}' --format json
```

A good third milestone is this command producing useful documentation:

```bash
demo-skill skill-md > SKILL.md
```

