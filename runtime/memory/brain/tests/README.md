# Brain System Tests

**Status:** Planned
**Priority:** Medium

## Purpose

Comprehensive tests for the brain system to ensure reliability and correctness.

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_validator.py   # Metadata validator tests
│   ├── test_template.py    # Template generator tests
│   ├── test_parser.py      # Query parser tests
│   └── test_schema.py      # Schema validation tests
├── integration/             # Integration tests
│   ├── test_ingestion.py   # Metadata ingestion tests
│   ├── test_query.py       # Query integration tests
│   └── test_databases.py   # Database integration tests
└── e2e/                     # End-to-end tests
    ├── test_full_workflow.py
    └── test_ai_integration.py
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=9-brain tests/

# Run specific test
pytest tests/unit/test_validator.py
```

## Test Coverage Goals

- Unit tests: >90% coverage
- Integration tests: All major workflows
- E2E tests: Critical user paths

## Status

⏳ Pending implementation
