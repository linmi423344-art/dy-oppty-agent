# dy-oppty-agent

Douyin Shop Opportunity Center Agent scaffold.

## Overview

This repository is the initial scaffold for a Playwright-based browser worker + ETL + selection engine targeting Douyin Shop's 商机中心 workflow.

Planned navigation path reference (no automation implemented yet):

- 抖店 -> 商品 -> 商机中心
- Module: 潜力爆品
- Window: 7天
- Loop categories and use export-first flow

## Requirements

- Python 3.11
- pip

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
playwright install
```

## CLI Usage

Run via module entrypoint:

```bash
python -m oppty_agent.cli --help
```

### Login stub

Opens a persistent browser profile and navigates to the configured base URL, then waits until you close the browser process.

```bash
python -m oppty_agent.cli login --profile-dir data/profile
```

### Run stub

Creates a run id, prepares `data/runs/<run_id>/`, writes `run_manifest.json`, and exits.

```bash
python -m oppty_agent.cli run --config oppty_agent/config/example.yaml
```

### ETL stub

```bash
python -m oppty_agent.cli etl --run-id <run_id>
```

### Selection stub

```bash
python -m oppty_agent.cli select --run-id <run_id> --config oppty_agent/config/example.yaml
```

## Development checks

```bash
ruff check .
pytest -q
```
