# Blackbox5 Engine Tests

This directory contains all tests for the Blackbox5 engine.

## Directory Structure

```
tests/
├── unit/              # Unit tests for individual components
│   ├── test_agent_output_bus.py
│   ├── test_agent_coordination.py
│   ├── test_error_handling.py
│   └── test_managerial_agent.py
├── integration/       # Integration tests
└── README.md          # This file
```

## Component-Specific Tests

Some components maintain their tests co-located within their directories:

- `core/safety/tests/` - Safety system tests
- `core/orchestration/tests/` - Orchestration tests
- `core/agents/definitions/core/test_*.py` - Agent core tests
- `core/interface/handlers/tests/` - Handler tests

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=core tests/
```

## Test Naming Conventions

- Unit tests: `test_<component>_<scenario>.py`
- Integration tests: `test_integration_<feature>.py`
- Test functions: `test_<functionality>_<condition>()`

## Adding New Tests

1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Follow existing naming conventions
4. Include docstrings describing what is being tested
