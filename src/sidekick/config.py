name = "Sidekick"
models = [
    "google-gla:gemini-2.5-pro-exp-03-25",
    "openai:gpt-4o",
    "openai:o3-mini",
    "anthropic:claude-3-7-sonnet-latest",
    "google-gla:gemini-2.0-flash",
]
model_pricing = {
    # No public pricing yet, so use 2.0-flash numbers
    "google-gla:gemini-2.5-pro-exp-03-25": {
        "input": 0.10,
        "cached_input": 0.025,
        "output": 0.40,
    },
    "google-gla:gemini-2.0-flash": {
        "input": 0.10,
        "cached_input": 0.025,
        "output": 0.40,
    },
    "openai:o3-mini": {
        "input": 1.10,
        "cached_input": 0.55,
        "output": 4.40,
    },
    "openai:gpt-4o": {
        "input": 2.50,
        "cached_input": 1.25,
        "output": 10.00,
    },
    "anthropic:claude-3-7-sonnet-latest": {
        "input": 3.00,
        "cached_input": 1.50,
        "output": 15.00,
    },
}
default_model = models[0]
