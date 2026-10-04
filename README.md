# OpsBuddy

OpsBuddy is a small troubleshooting helper for a close friend who is learning DevOps. When Kubernetes, Docker, or a CI/CD pipeline fails, it turns the error or logs into a plain-language explanation and a few practical next steps.

The first version uses a local Ollama model. Diagnostic text stays on the computer running Ollama; OpsBuddy does not store submitted notes. Remove passwords, tokens, and other secrets before pasting logs. OpsBuddy removes next steps that contain known potentially system-changing actions or common shell commands, and only shows commands from a small read-only allowlist. Model output still needs review.

## Run it locally

You will need Python 3.11 or newer and [Ollama](https://ollama.com/) installed and running.

Pull the default model once:

```bash
ollama pull qwen2.5-coder:3b
```

Then, from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

To use a different Ollama model or local Ollama server, set `OLLAMA_MODEL` or `OLLAMA_BASE_URL` before starting the app. For example:

```bash
OLLAMA_MODEL=qwen2.5:3b uvicorn app.main:app --reload
```

## Run the tests

```bash
pytest -q
ruff check .
```

## What it does

- Accepts diagnostic text for Kubernetes, Docker, CI/CD, or another issue.
- Asks the local model for a short explanation, likely causes, ordered checks, and commands to review.
- Displays model output as text rather than interpreting it as HTML.
- Does not execute commands or save submitted diagnostic text.

OpsBuddy is an aid for learning and investigation, not a replacement for checking official documentation or understanding the effect of a command before running it.
