# Sidekick (Beta)

Your agentic CLI developer.

## Overview

Sidekick is an agentic CLI-based AI tool inspired by Claude Code, Copilot, Windsurf and Cursor. It's meant
to be an open source alternative to these tools, providing a similar experience but with the flexibility of
using different LLM providers while keeping the agentic workflow.

Sidekick is currently in beta and under active development. I'd love your ideas and feedback.

## Features

- No vendor lock-in. Use whichever LLM provider you prefer.
- Use /undo when AI breaks things.
- JIT-style system prompt injection ensures Sidekick doesn't lose the plot.
- Per-project guide. Adjust Sidekick's behavior to suit your needs.
- CLI-first design. Ditch the clunky IDE.
- Easily switch between models in the same session.
- Cost and token tracking.
- Web searching and fetching built-in.
- Per command or per session confirmation skipping.

## Roadmap

- Tests 😅
- More LLM providers, including Ollama
- Plugin system (custom tools and agents)
- MCP Support

## Quick Start

Install Sidekick and Playwright:

```
pip install sidekick-cli
python -m playwright install
```

Startup Sidekick and configure LLM providers:

```
sidekick
```

## Configuration

After initial setup, Sidekick saves a config file to `~/.config/sidekick.json`. You can open and 
edit this file as needed. Future updates will make editing easier directly from within Sidekick.

### Available Commands

- `/help` - Show available commands
- `/yolo` - Toggle "yolo" mode (skip tool confirmations)
- `/clear` - Clear message history
- `/compact` - Summarize message history and clear old messages
- `/model` - List available models
- `/model <num>` - Switch to a specific model (by index)
- `/undo` - Undo most recent changes
- `/dump` - Show current message history (for debugging)
- `exit` - Exit the application

## Customization

Sidekick supports the use of a "guide". This is a `SIDEKICK.md` file in the project root that contains
instructions for Sidekick. Helpful for specifying tech stack, project structure, development
preferences etc.

## Telemetry

Sidekick uses [Sentry](https://sentry.io/) for error tracking and usage analytics. You can disable this by
starting with the `--no-telemetry` flag.

```
sidekick --no-telemetry
```

## Installation

### Using pip

```bash
pip install sidekick-cli
```

For the best web search and fetching results, install Playwright:

```bash
python -m playwright install
```

### From Source

1. Clone the repository
2. Install dependencies: `pip install .` (or `pip install -e .` for development)
3. Install Playwright: `python -m playwright install`

## Development

```bash
# Install development dependencies
make install

# Run linting
make lint

# Run tests
make test
```

## License

MIT
