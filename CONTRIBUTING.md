# Contributing

Thanks for helping improve Heisenberg Network Monitor.

## Development setup

1. Create and activate a Python 3.13 virtual environment.
2. Install runtime dependencies with `pip install -r requirements.txt`.
3. Install development dependencies with `pip install -r requirements-dev.txt`.
4. Run tests with `pytest`.
5. Start the app with `python -m app.main`.

## Contribution guidelines

- Keep UI thin and route behavior through actions and services.
- Prefer reusable engines over page-specific logic.
- Add tests for new service and engine behavior where practical.
- Do not commit runtime databases, logs, exports, or personal config.
- Use sample data only. Do not add real credentials, IP inventories, or private references.

## Pull requests

- Include a concise problem statement and approach.
- Update docs for user-facing or architectural changes.
- Keep changes focused and reviewable.

