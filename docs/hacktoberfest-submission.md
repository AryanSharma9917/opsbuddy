# Hacktoberfest Weekend Challenge: Build for a Friend

## What I built

OpsBuddy is a local troubleshooting helper for a friend or teammate learning
DevOps. It turns a messy Docker, Kubernetes, or CI/CD error into a short,
plain-language explanation, likely causes, and a few careful next checks to
review.

The project is intentionally simple: it uses a local model, keeps the work on the
user's machine, and avoids pretending it has more context than it actually does.

## Why this helps a friend

A lot of people learning DevOps do not need a full production dashboard. They
need a calmer, safer way to understand what a failing error message actually
means.

OpsBuddy helps by turning raw logs or issues into:

- a short summary of the issue
- possible causes based on the available evidence
- ordered checks to inspect next
- read-only commands to review before changing anything

This makes it useful for a friend, a teammate, or a beginner who is trying to
learn without getting overwhelmed by tooling and jargon.

## Why open-source AI matters here

This project is built around local open-source AI because the user should keep the
workflow private and explainable. It keeps the diagnostic process grounded in
what the user actually provides, rather than sending everything to a black-box
service.

Open-source, local-first tooling matters when you are learning or debugging in a
real environment, especially when the goal is to understand the system instead of
just getting a magical answer.

## How it works

- accept diagnostic text from the user
- call a local Ollama model with a safety-focused system prompt
- ask for a summary, likely causes, and ordered checks
- return the result in a structured JSON format
- keep commands read-only and review-first

## How to run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ollama pull qwen2.5-coder:3b
uvicorn app.main:app --reload
```

Then open http://localhost:8000.

## Project links

- Repository: https://github.com/AryanSharma9917/opsbuddy
- Local app: http://localhost:8000

## Why this fits the challenge

This project is small, useful, and grounded in a real problem. It helps someone
who is learning or supporting infrastructure make better decisions without blindly
running commands or guessing at causes.
