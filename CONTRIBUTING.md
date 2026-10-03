# Contributing

Thanks for helping improve OpsBuddy.

## Ways to contribute

- improve the troubleshooting flow
- add better prompts or clearer output
- improve documentation and onboarding
- fix bugs or edge cases
- add tests for new behaviors

## Local setup

```bash
git clone https://github.com/AryanSharma9917/opsbuddy.git
cd opsbuddy
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Make sure Ollama is installed and running locally before starting the app.

## Validation

Before opening a pull request, run:

```bash
pytest -q
ruff check .
```

## Pull request expectations

- keep the change focused and explain the problem clearly
- include tests when behavior changes
- keep the patch easy to review
- document any environment-specific requirements

## Code of conduct

Please keep discussions respectful, practical, and focused on improving the
project for real users.
