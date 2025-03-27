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

You can either set these in your environment or create a `.env` file in your project directory.

## Usage

Start Sidekick by running:

```bash
sidekick
```

### Available Commands

- `/clear` - Clear message history
- `/dump` - Show current message history (for debugging)
- `/model` - List available models
- `/model <num>` - Switch to a specific model (by index)
- `exit` - Exit the application

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
