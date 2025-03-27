# Sidekick Research Tool

An interactive command-line research assistant powered by multiple LLM providers.

## Features

- Interactive REPL interface with multiline input support
- Rich terminal output with syntax highlighting and markdown formatting
- Support for multiple AI models (Google Gemini, OpenAI, Anthropic Claude)
- Built-in tools for:
  - Running shell commands
  - Reading and writing files
  - Fetching web content
- Session management with history tracking

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables (API keys)
3. Run the application: `python main.py`
4. Install Playwright for fetch tool: `python -m playwright install`

## Usage

Available commands:
- `/clear` - Clear message history
- `/dump` - Show current message history (debugging)
- `/help` - Show available commands
- `/model` - List available models
- `/model <num>` - Switch to a specific model

## Development

Run linting: `make lint`

## Ideas / Future Work

- "Sentiment" agent that checks if a tool call was intended when AI responds without calling a tool
