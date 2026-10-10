# Task2View code

Install, run, and test from this directory. The full description is in the [root README](../README.md).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,anthropic]"
cp .env.example .env   # put API keys here — gitignored
pytest

task2view run --code /path/to/repo --goal "..." --out runs/demo --llm anthropic:claude-sonnet-5-5
task2view plugins
```
