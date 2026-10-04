*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

I built OpsBuddy for my best friend, who is learning DevOps. When a Kubernetes pod keeps restarting, a Docker container exits unexpectedly, or a CI/CD run fails, it can be hard to know which part of the error matters or what to check first.

OpsBuddy is a small troubleshooting assistant for those moments. You choose the area you are working on, paste an error or a short piece of diagnostic output, and ask for help understanding it. It returns a plain-language summary, possible causes, next checks, and commands to review.

My friend has tried the app and shared feedback with me. I’m keeping their name and personal details private.

OpsBuddy is meant to help someone decide where to investigate next, not to claim a definitive diagnosis. It does not connect to a cluster, run commands, or make changes to a system.

## Demo

**Demo video:** [Add the video link here before publishing.]

The video will show a sanitized troubleshooting example entered into OpsBuddy and the resulting explanation and suggested checks. The app currently runs locally, so `localhost` is not a public demo link.

## Code

[OpsBuddy on GitHub](https://github.com/AryanSharma9917/opsbuddy)

## How I Built It

OpsBuddy has a small browser-based interface and a FastAPI backend. The backend sends the submitted diagnostic text to Ollama running on the same computer and asks for a structured response. The default model is the open-weight `qwen2.5-coder:3b`.

While testing, I saw the model suggest restarting a Kubernetes pod even though the prompt asked it to stick to read-only troubleshooting. That made it clear that prompt wording alone was not enough. I added backend checks that remove known system-changing actions and common shell commands from the suggested steps, limit displayed commands to a small read-only allowlist, and ask for more information when the input is too vague to support an analysis.

These checks are safeguards, not a guarantee that every response is correct or suitable for every environment. OpsBuddy never executes the suggested commands, and users should review them before deciding whether to run them. Diagnostic text is sent to the local Ollama service; users should still remove passwords, tokens, and other secrets before sharing logs.

## Why Does Open Innovation Matter?

Troubleshooting notes can contain details people would rather not send to a hosted AI service. With the default setup, OpsBuddy sends the request to Ollama on the same computer instead of a hosted AI API. Once Ollama and the model are installed, the analysis can run locally.

Using an open-weight model also means the project is not tied to one proprietary AI API. A user can choose another compatible local model and decide what works on their own machine. The trade-off is that local inference needs enough computing resources, and the model can still give incorrect or overconfident answers.

For this project, open innovation makes it possible to build a useful local-first tool while giving the person using it more control over their diagnostic data and model choice.

## My Agent Session

This section is optional. I’m not including a DevRelay session link.
