# Sidekick (Beta)

[![PyPI version](https://badge.fury.io/py/sidekick-cli.svg)](https://badge.fury.io/py/sidekick-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

![Sidekick Demo](screenshot.gif)

Your agentic CLI developer.

## Overview

Sidekick is an agentic CLI-based AI tool inspired by Claude Code, Copilot, Windsurf and Cursor. It's meant
to be an open source alternative to these tools, providing a similar experience but with the flexibility of
using different LLM providers (Anthropic, OpenAI, Google Gemini) while keeping the agentic workflow.

*Sidekick is currently in beta and under active development. Please [report issues](https://github.com/geekforbrains/sidekick-cli/issues) or share feedback!*

## Features

- No vendor lock-in. Use whichever LLM provider you prefer.
- MCP support
- Use /undo when AI breaks things.
- Easily switch between models in the same session.
- JIT-style system prompt injection ensures Sidekick doesn't lose the plot.
- Per-project guide. Adjust Sidekick's behavior to suit your needs.
- CLI-first design. Ditch the clunky IDE.
- Cost and token tracking.
- Per command or per session confirmation skipping.

## Roadmap

- Tests 😅
- More LLM providers, including Ollama

## Quick Start

Install Sidekick.

```
pip install sidekick-cli
```

On first run, you'll be asked to configure your LLM providers.

```
sidekick
```

## Configuration

After initial setup, Sidekick saves a config file to `~/.config/sidekick.json`. You can open and 
edit this file as needed. Future updates will make editing easier directly from within Sidekick.

### MCP Support

Sidekick supports Model Context Protocol (MCP) servers. You can configure MCP servers in your `~/.config/sidekick.json` file:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
      }
    }
  }
}
```

MCP servers extend the capabilities of your AI assistant, allowing it to interact with additional tools and data sources. Learn more about MCP at [modelcontextprotocol.io](https://modelcontextprotocol.io/).

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

## Requirements

- Python 3.10 or higher
- Git (for undo functionality)

## Installation

### Using pip

```bash
pip install sidekick-cli
```

### From Source

1. Clone the repository
2. Install dependencies: `pip install .` (or `pip install -e .` for development)

## Development

```bash
# Install development dependencies
make install

# Run linting
make lint

# Run tests
make test
```

## Release Process

When preparing a new release:

1. Update version numbers in:
   - `pyproject.toml`
   - `src/sidekick/constants.py` (APP_VERSION)

2. Commit the version changes:
   ```bash
   git add pyproject.toml src/sidekick/constants.py
   git commit -m "chore: bump version to X.Y.Z"
   ```

3. Create and push a tag:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

4. Create a GitHub release:
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes "Release notes here"
   ```

5. Merge to main branch and push to trigger PyPI release (automated)

### Commit Convention

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Test additions or modifications
- `chore:` - Maintenance tasks (version bumps, etc.)
- `build:` - Build system changes
- `ci:` - CI configuration changes

## Links

- [PyPI Package](https://pypi.org/project/sidekick-cli/)
- [GitHub Issues](https://github.com/geekforbrains/sidekick-cli/issues)
- [GitHub Repository](https://github.com/geekforbrains/sidekick-cli)

## License

MIT
