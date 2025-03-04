# Project Guidelines

## Current Focus
- Creating a new `disk-space` demo

## Run Commands

### Disk Space

### LLM Training Game

- Generate prediction data: `uv run llm-training-game/generate.py`
- Run web server: `uv run llm-training-game/serve.py`
- Run terminal UI: `uv run llm-training-game/tui.py`
- Run TUI as web app: `uv run llm-training-game/tui.py --web`
- Run Streamlit app: `uv run llm-training-game/app.py`

## Code Style

### Structure & Imports
- Imports order: standard library → third-party → local modules
- Organize imports alphabetically within each section
- Separate main functionality into distinct modules

### Naming & Typing
- Functions/variables: `snake_case`  
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Use docstrings for type documentation

### Error Handling
- Use try/except with specific exception types
- Include descriptive error messages
- UI-level errors should be user-friendly

### Documentation
- Add docstrings to functions with parameter descriptions
- Include inline comments for complex logic
- Keep README updated with usage instructions
