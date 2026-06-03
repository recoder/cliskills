# cliskill

`cliskill` is a Python framework for building contract-first command-line tools
intended for LLM agents and automation systems.

The project is in its initial skeleton phase. The first target is a demo skill
that can emit a machine-readable manifest:

```bash
demo-skill manifest --format json
```

It can also run registered commands with JSON input:

```bash
demo-skill run echo --json '{"text":"hello"}' --format json
```

## Authoring

```python
from pydantic import BaseModel

from cliskill import Skill, SkillContext

skill = Skill(
    name="demo-skill",
    version="0.1.0",
    description="Demo skill.",
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
def echo(input_data: EchoInput, ctx: SkillContext) -> EchoOutput:
    return EchoOutput(text=input_data.text, length=len(input_data.text))


if __name__ == "__main__":
    skill.main()
```

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy
```
