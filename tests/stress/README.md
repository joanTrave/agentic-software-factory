# Stress tests

Load profiles, one scenario file per critical endpoint, run on demand against a deployed
environment. These are not part of the default test run: `pyproject.toml`'s
`[tool.pytest.ini_options]` excludes this directory (`--ignore=tests/stress`) so a slow load test
never blocks the `docker compose run --rm test` gate.

Run a scenario explicitly, e.g.:

```sh
pytest tests/stress/<scenario_file>.py
```

No scenario files exist yet — this directory is a placeholder for the first bounded context that
needs one.
