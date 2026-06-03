# cliskill

`cliskill` is a Python framework for building contract-first command-line tools
intended for LLM agents and automation systems.

The project is in its initial skeleton phase. The first target is a demo skill
that can emit a machine-readable manifest:

```bash
demo-skill manifest --format json
```

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy
```
