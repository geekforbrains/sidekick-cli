# Sidekick

Your agentic CLI developer.

## Overview

Sidekick is an AI agent that helps you with development tasks. It's powered by multiple LLM providers 
and provides a seamless interactive experience in your terminal, allowing you to get help with coding, 
run commands, manage files, and search the web without leaving your workflow.

## Features

- No vendor lock-in. Use whichever LLM provider you prefer.
- CLI-first design. Ditch the clunky IDE.
- Easily switch between models in the same session.
- Cost and token tracking.
- Web searching and fetching built-in.

## Installation

### Using pip

```bash
pip install sidekick-cli
```

For the best fetching results, install the Playwright:

```bash
python -m playwright install
```

### From Source

1. Clone the repository
2. Install dependencies: `pip install .` (or `pip install -e .` for development)
3. Install Playwright: `python -m playwright install`

## Configuration

You'll need to set API keys for each of the providers you want to use.

```bash
# For OpenAI models
OPENAI_API_KEY=your_openai_key

# For Google Gemini models
GOOGLE_API_KEY=your_google_key

# For Anthropic Claude models
ANTHROPIC_API_KEY=your_anthropic_key
```

You can either set these in your environment, create a `.env` file in your project directory, or add them to your config file at `~/.config/sidekick.json`.

## Usage

Start Sidekick by running:

```bash
sidekick
```

### Command Line Options

- `--logfire` - Enable Logfire tracing
- `--no-telemetry` - Disable telemetry collection

### Available Commands

- `/clear` - Clear message history
- `/dump` - Show current message history (for debugging)
- `/help` - Show available commands
- `/model` - List available models
- `/model <num>` - Switch to a specific model (by index)
- `/undo` - Undo most recent changes
- `/yolo` - Run commands without confirmation
- `exit` - Exit the application

## Telemetry

Sidekick collects anonymous usage data and error reports to help us improve the product. This data is stripped of all personally identifiable information and sensitive content. We never track your actual prompts or the content of your conversations.

### What We Collect

- Anonymous session ID
- Non-sensitive command usage statistics
- Error reports (without sensitive information)
- Basic environment information (Python version, OS)

### Opting Out

You can disable telemetry collection by running Sidekick with the `--no-telemetry` flag:

```bash
sidekick --no-telemetry
```

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
