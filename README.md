# dy-oppty-agent

Automation scaffold for export-first Opportunity Center data collection.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

## CLI

```bash
python -m oppty_agent.cli --help
python -m oppty_agent.cli login --config oppty_agent/config/example.yaml
python -m oppty_agent.cli run --config oppty_agent/config/example.yaml
```

## Configuration

See `oppty_agent/config/example.yaml` for all keys. Existing keys are preserved and include login credentials, headless mode, output directory, UI categories, download timeout, and risk keywords.

## Development checks

```bash
ruff check .
pytest -q
```
