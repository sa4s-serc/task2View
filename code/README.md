# Task2View code

Install, run, and test from this directory. The full description is in the [root README](../README.md).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # GEMINI_API_KEY — gitignored
pytest

task2view run --code /path/to/repo --goal "..." --out runs/demo
task2view plugins
```

`--config pipeline.example.yaml` selects scoper / extractor / diagram language. CLI flags override.
